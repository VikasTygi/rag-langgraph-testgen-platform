def build_robot_prompt(user_prompt: str, retrieved_context: str = "") -> str:
    return f"""
You are an expert Robot Framework automation engineer.

Generate a complete Robot Framework automation script for the following user request.

USER REQUEST:
{user_prompt}

RELEVANT CONTEXT FROM EXISTING AUTOMATION REPOSITORY:
{retrieved_context}

IMPORTANT:
You must strongly follow the style, keyword names, libraries, variables, and patterns from the retrieved context.
If retrieved context contains reusable keywords like Login To Ruckus Cloud API, Create Venue API, or Verify Venue Name, reuse those patterns.

ROBOT FRAMEWORK REQUIREMENTS:
- Return only raw Robot Framework code.
- Do not use markdown.
- Do not use triple backticks.
- Do not add explanation outside the code.
- Include *** Settings *** section.
- Include *** Variables *** section if variables are needed.
- Include *** Keywords *** section if reusable keywords are needed.
- Include *** Test Cases *** section.
- Use readable keyword names.
- Add verification/assertion steps.
- Generated code must be valid for robot --dryrun.

ROBOT SYNTAX RULES:
- Do not define keyword arguments on the same line as the keyword name.
- Always define keyword arguments using [Arguments] inside the keyword body.

Correct keyword style:
Create Venue API
    [Arguments]    ${{token}}    ${{venue_name}}
    Log    ${{venue_name}}

Incorrect keyword style. Do not generate this:
Create Venue API    ${{token}}    ${{venue_name}}
    Log    ${{venue_name}}

REQUESTSLIBRARY RULES:
- If generating API automation, prefer RequestsLibrary.
- Use Create Session before API calls.
- Use POST On Session, GET On Session, PUT On Session, DELETE On Session.
- Use Create Dictionary for payloads and headers.
- Do not use Evaluate for simple dictionaries.
- Pass tokens as keyword arguments or return values.
- Do not use undefined variables.
- Use correct spacing between Robot keyword arguments.

GOOD API STYLE EXAMPLE:
*** Settings ***
Library    RequestsLibrary

*** Variables ***
${{BASE_URL}}       https://ruckus.cloud
${{USERNAME}}       admin
${{PASSWORD}}       password
${{VENUE_NAME}}     Auto_Venue_001

*** Keywords ***
Login To Ruckus Cloud API
    Create Session    ruckus    ${{BASE_URL}}
    ${{payload}}=    Create Dictionary    username=${{USERNAME}}    password=${{PASSWORD}}
    ${{response}}=    POST On Session    ruckus    /login    json=${{payload}}
    Should Be Equal As Integers    ${{response.status_code}}    200
    ${{token}}=    Set Variable    ${{response.json()["token"]}}
    RETURN    ${{token}}

Create Venue API
    [Arguments]    ${{token}}    ${{venue_name}}
    ${{headers}}=    Create Dictionary    Authorization=Bearer ${{token}}
    ${{payload}}=    Create Dictionary    name=${{venue_name}}    description=Created from automation
    ${{response}}=    POST On Session    ruckus    /venues    json=${{payload}}    headers=${{headers}}
    Should Be True    ${{response.status_code}} == 200 or ${{response.status_code}} == 201
    RETURN    ${{response.json()}}

Verify Venue Name
    [Arguments]    ${{venue}}    ${{venue_name}}
    Should Be Equal As Strings    ${{venue["name"]}}    ${{venue_name}}

*** Test Cases ***
Create Venue On Ruckus Cloud
    ${{token}}=    Login To Ruckus Cloud API
    ${{venue}}=    Create Venue API    ${{token}}    ${{VENUE_NAME}}
    Verify Venue Name    ${{venue}}    ${{VENUE_NAME}}

Generate only the final Robot Framework code now.
"""