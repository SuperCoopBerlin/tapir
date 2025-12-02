from tapir.rizoma.exceptions import CoopsPtRequestException
from tapir.rizoma.services.coops_pt_request_handler import CoopsPtRequestHandler


class GroupAffiliationChecker:
    @classmethod
    def is_member_affiliation_to_group_active(
        cls, external_id: str, group_name: str
    ) -> bool | None:
        # When getting the member data from the /members API end point, we get a _currentState field that tells use
        # if a member belongs to a certain group. However, this group affiliation may be inactive.
        # That information is only available through a members/ID/member_states call
        # Returns True if the member is in the group and active
        # Returns False if the member is in the group but inactive
        # Returns None if the member is not in the group

        response = CoopsPtRequestHandler.get(f"members/{external_id}/member_states")
        if response.status_code != 200:
            raise CoopsPtRequestException("Failed to get user list from coops.pt")

        # Example element from the response.data list:
        # {'_created_at': '2025-10-13T15:47:15.744Z',
        # '_deleted_at': None,
        # '_id': 'e3f21320-bb90-4bba-8e55-dad3a13013a9',
        # '_memberStateName': 'Consumidores',
        # '_updated_at': '2025-11-19T14:39:29.263Z',
        # 'aquiredShares': 50,
        # 'date': '2020-11-18T00:00:00Z',
        # 'dateEnd': None,
        # 'memberStateNameId': '2895586f-66cf-4d72-b6d9-e939b3ed88b8',
        # 'shareReturnStatus': 'Não decidiu',
        # 'status': 'Activo'}

        group_states = response.json()["data"]
        for state in group_states:
            if state["_memberStateName"] != group_name:
                continue
            return state["status"] == "Activo"

        return None
