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

"""
An example of a template function is in /vrtemplates/race.py, which includes detailed comments on the processing steps. The general structure of a template function is as follows:
1 - Load session data using FastF1 based on the provided year, country and session name.
2 - Filter the session laps to include only the selected drivers (if any).
3 - Optionally exclude laps affected by safety car or virtual safety car periods.
4 - Ensure lap times are in a consistent format (e.g. seconds) for plotting.
5 - Generate a Plotly figure (e.g. scatter plot of lap time vs lap number) with appropriate styling and hover information.
6 - Convert the Plotly figure to a JSON-serialisable format for inclusion in the API response.
7 - Return a structured JSON response containing the visualisation data and any relevant metadata (e.g
title, description) for the frontend to render the visualisation builder output.

The vr_create_view function routes incoming requests to the appropriate template function based on the provided template ID, while the session_vrdetails_view function retrieves driver and team information for a given session to support frontend selection in the visualisation builder.
Furthermore, the template function is assigned to a template ID, which can be routed below. The meanings of each one can be found in Appendix A.

"""

@csrf_exempt
def vr_create_view(request):
    """
    Routes a visualisation/report request to the correct template handler.

    The request body includes a template ID and input parameters, which are
    extracted and passed to the corresponding backend function responsible
    for generating the required visualisation.

    Args:
        request: HTTP request containing templateId and input values.

    Returns:
        JsonResponse: Result from the selected template, or an error if the
        template ID is not recognised.
    """
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
    """
    Returns the drivers and teams for a given session to support frontend
    selection in the visualisation builder.

    Session results are loaded via FastF1 and parsed to extract driver
    abbreviations and a unique list of team names.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session_name (str): Session type.

    Returns:
        JsonResponse: Driver abbreviations and unique team names for the session.
    """
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