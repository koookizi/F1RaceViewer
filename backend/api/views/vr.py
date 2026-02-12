from django.http import JsonResponse
import fastf1
from functools import lru_cache
import json
from django.views.decorators.csrf import csrf_exempt
from api.vr_templates.race import (
    vr_pace_1,
    vr_pace_2,
    vr_pace_3,
    vr_pace_4,
    vr_positions_3
)
from api.vr_templates.driver import (
    vr_dsp_1,
    vr_dsp_2,
    vr_dsp_3,
    vr_dvt_1,
    vr_dvt_2,
    vr_dvt_3,
    vr_dc_1,
    vr_dc_2,
    vr_dc_3
)
from api.vr_templates.team import (
    vr_tsp_1,
    vr_tsp_2,
    vr_tsp_3,
    vr_tca_1,
    vr_tca_2,
    vr_tca_3,
    vr_tpc_1,
    vr_tpc_2,
)

__all__ = [
    "vr_create_view",
    "session_vrdetails_view"
]

@csrf_exempt
def vr_create_view(request):
    body = json.loads(request.body)
    template_id = body["templateId"]
    inputs = body.get("inputs", {})

    if template_id == "t1":
        return vr_pace_1(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t2":
        return vr_pace_2(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t3":
        return vr_pace_3(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t4":
        return vr_pace_4(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t23":
        return vr_positions_3(inputs)
    elif template_id == "t24":
        return vr_tsp_1(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t25":
        return vr_tsp_2(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t26":
        return vr_tsp_3(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t27":
        return vr_tca_1(int(inputs.get("seasonFrom", 0)), inputs.get("seasonTo", ""), inputs.get("team", ""), inputs)
    elif template_id == "t28":
        return vr_tca_2(int(inputs.get("seasonFrom", 0)), inputs.get("seasonTo", ""), inputs.get("team", ""), inputs)
    elif template_id == "t29":
        return vr_tca_3(int(inputs.get("seasonFrom", 0)), inputs.get("seasonTo", ""), inputs.get("team", ""), inputs)
    elif template_id == "t30":
        return vr_tpc_1(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t31":
        return vr_tpc_2(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t32":
        return vr_dsp_1(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t33":
        return vr_dsp_2(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t34":
        return vr_dsp_3(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t35":
        return vr_dvt_1(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t36":
        return vr_dvt_2(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t37":
        return vr_dvt_3(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t38":
        return vr_dc_1(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t39":
        return vr_dc_2(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)
    elif template_id == "t40":
        return vr_dc_3(int(inputs.get("season", 0)), inputs.get("driver", ""), inputs)

    return JsonResponse({"error": "Unknown templateId"}, status=400)

@lru_cache(maxsize=32)
def session_vrdetails_view(request, year: int, country: str, session_name: str):
    session = fastf1.get_session(year, country, session_name)

    session.load(telemetry=False)

    drivers = []
    teams = []

    results_df = session.results

    for _, row in results_df.iterrows():
        drivers.append(row.get("Abbreviation", ""),)
        teams.append(row.get("TeamName", ""))    

    teams = list(dict.fromkeys(teams))

    return JsonResponse({
         "drivers": drivers,
         "teams": teams,
         })