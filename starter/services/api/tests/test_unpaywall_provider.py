import pytest
import respx

from citetrace_api.providers.unpaywall import UnpaywallProvider


@pytest.mark.anyio
async def test_get_oa_locations():
    provider = UnpaywallProvider(contact_email="test@example.com")
    
    with respx.mock:
        respx.get("https://api.unpaywall.org/v2/10.123/abc?email=test@example.com").respond(
            status_code=200,
            json={
                "doi": "10.123/abc",
                "is_oa": True,
                "best_oa_location": {
                    "url": "https://example.com/pdf",
                    "url_for_pdf": "https://example.com/pdf",
                    "is_best": True,
                    "host_type": "publisher"
                },
                "oa_locations": []
            }
        )
        
        result = await provider.get_oa_locations("10.123/abc")
        assert result.doi == "10.123/abc"
        assert result.is_oa is True
        assert result.best_oa_location.host_type == "publisher"
