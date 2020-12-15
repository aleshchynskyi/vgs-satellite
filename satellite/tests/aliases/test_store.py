import uuid

from satellite.aliases.generators import AliasGeneratorType
from satellite.aliases.store import AliasStore
from satellite.db import get_session
from satellite.db.models.alias import Alias


def make_alias(store: bool) -> Alias:
    value = str(uuid.uuid4())
    alias = Alias(
        value=value,
        alias_generator=AliasGeneratorType.UUID,
        public_alias=f'public_{value}',
    )
    session = get_session()
    session.add(alias)
    session.commit()

    return alias


def test_get_by_value():
    alias = make_alias(True)
    store = AliasStore()
    assert store.get_by_value(alias.public_alias) is None
    assert store.get_by_value(alias.value) == alias


def test_get_by_alias():
    alias = make_alias(True)
    store = AliasStore()
    assert store.get_by_alias(alias.value) is None
    assert store.get_by_alias(alias.public_alias) == alias


def test_save():
    alias = make_alias(False)
    store = AliasStore()

    store.save(alias)

    stored_alias = get_session().query(Alias).filter(Alias.id == alias.id).first()
    assert stored_alias == alias


def test_get_by_value_with_ttl():
    alias = make_alias(False)
    store = AliasStore(60)
    store.save(alias)
    assert store.get_by_value(alias.value) == alias
    assert AliasStore().get_by_value(alias.value) is None


def test_get_by_value_with_ttl_expired():
    alias = make_alias(False)
    store = AliasStore(-1)
    store.save(alias)
    assert store.get_by_value(alias.value) is None


def test_get_by_alias_with_ttl():
    alias = make_alias(False)
    store = AliasStore(60)
    store.save(alias)
    assert store.get_by_alias(alias.public_alias) == alias
    assert AliasStore().get_by_alias(alias.public_alias) is None


def test_get_by_alias_with_ttl_expired():
    alias = make_alias(False)
    store = AliasStore(-1)
    store.save(alias)
    assert store.get_by_alias(alias.public_alias) is None


def test_cleanup():
    session = get_session()
    session.query(Alias).delete()
    session.commit()

    persistent_store = AliasStore()
    alias1 = make_alias(False)
    persistent_store.save(alias1)

    volatile_store = AliasStore(60)
    alias2 = make_alias(False)
    volatile_store.save(alias2)

    alias3 = make_alias(False)
    AliasStore(-1).save(alias3)

    assert AliasStore.cleanup() == 1
    persistent_store.get_by_value(alias1.value) is not None
    volatile_store.get_by_value(alias2.value) is not None
    volatile_store.get_by_value(alias3.value) is None
