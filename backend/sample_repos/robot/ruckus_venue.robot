*** Settings ***
Documentation    Sample Ruckus Cloud venue automation using RequestsLibrary.
Library          RequestsLibrary

*** Variables ***
${BASE_URL}       https://ruckus.cloud
${USERNAME}       admin
${PASSWORD}       password
${VENUE_NAME}     Auto_Venue_001

*** Keywords ***
Login To Ruckus Cloud API
    [Documentation]    Login to Ruckus Cloud and return auth token.
    Create Session    ruckus    ${BASE_URL}
    ${payload}=    Create Dictionary    username=${USERNAME}    password=${PASSWORD}
    ${response}=    POST On Session    ruckus    /login    json=${payload}
    Should Be Equal As Integers    ${response.status_code}    200
    ${token}=    Set Variable    ${response.json()["token"]}
    RETURN    ${token}

Create Venue API
    [Arguments]    ${token}    ${venue_name}
    [Documentation]    Create venue using Ruckus Cloud API.
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${payload}=    Create Dictionary    name=${venue_name}    description=Created from automation
    ${response}=    POST On Session    ruckus    /venues    json=${payload}    headers=${headers}
    Should Be True    ${response.status_code} == 200 or ${response.status_code} == 201
    RETURN    ${response.json()}

Verify Venue Name
    [Arguments]    ${venue}    ${venue_name}
    Should Be Equal As Strings    ${venue["name"]}    ${venue_name}

*** Test Cases ***
Create Venue On Ruckus Cloud
    ${token}=    Login To Ruckus Cloud API
    ${venue}=    Create Venue API    ${token}    ${VENUE_NAME}
    Verify Venue Name    ${venue}    ${VENUE_NAME}