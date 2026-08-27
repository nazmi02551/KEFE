from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.session_renewal import RenewalResolutionStatus
from kefe_api.modules.identity.service import IdentityService


def test_guest_creation_persists_matching_renewal_family() -> None:
    repository = InMemoryIdentityRepository()
    service = IdentityService(
        repository=repository,
        guest_token_ttl_days=30,
    )

    credential = service.create_guest()

    assert credential.renewal_token is not None
    assert credential.rotation_counter == 0
    resolution = repository.resolve_renewal(
        renewal_token_hash=service._hash_token(credential.renewal_token),
        now=credential.expires_at,
    )
    assert resolution.status is RenewalResolutionStatus.ACTIVE
    assert resolution.snapshot is not None
    assert resolution.snapshot.actor_id == credential.actor_id
    assert resolution.snapshot.rotation_counter == 0
