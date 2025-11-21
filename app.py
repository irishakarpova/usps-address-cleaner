import streamlit as st
import requests

def smarty_validate(street, city, state, zipcode, auth_id, auth_token):
    url = "https://us-street.api.smarty.com/street-address"

    params = {
        "auth-id": auth_id,
        "auth-token": auth_token,
        "street": street,
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "match": "invalid"  
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, f"HTTP error {response.status_code}"

    data = response.json()

    if not data:
        return None, "Address not found"

    result = data[0]
    analysis = result.get("analysis", {})
    dpv = analysis.get("dpv_match_code")  

    comp = result["components"]

    cleaned = {
        "primary_number": comp.get("primary_number"),
        "street_name": comp.get("street_name"),
        "street_suffix": comp.get("street_suffix"),
        "city": comp.get("city_name"),
        "state": comp.get("state_abbreviation"),
        "zipcode": comp.get("zipcode"),
        "plus4": comp.get("plus4_code"),
        "dpv": dpv
    }

    # Determine validity message
    if dpv == "Y":
        return cleaned, None  # fully valid
    elif dpv == "S":
        return cleaned, "Missing secondary unit (apartment/suite)"
    elif dpv == "D":
        return cleaned, "Primary number missing/invalid"
    elif dpv == "N":
        return None, "Invalid address (DPV=N)"
    else:
        return cleaned, "Address not found in USPS DPV, suggested closest match"


st.title("USPS Address Validator (Smarty)")

auth_id = st.text_input("Smarty AUTH-ID")
auth_token = st.text_input("Smarty AUTH-TOKEN", type="password")

street = st.text_input("Street")
city = st.text_input("City")
state = st.text_input("State (2 letters, e.g., TX)")
zip5 = st.text_input("ZIP Code")

# Session state to preserve results across clicks
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None

def run_validation():
    cleaned, error = smarty_validate(street, city, state, zip5, auth_id, auth_token)
    st.session_state.last_result = cleaned
    st.session_state.last_error = error

st.button("Validate Address", on_click=run_validation)

# Display results
if st.session_state.last_error and st.session_state.last_result is None:
    st.error("Error" + st.session_state.last_error)

elif st.session_state.last_result:
    if st.session_state.last_error:
        st.warning("⚠ " + st.session_state.last_error)
    else:
        st.success("Valid USPS address!")

    # Display suggested/corrected address
    res = st.session_state.last_result
    formatted_address = f"{res['primary_number']} {res['street_name']} {res['street_suffix']}\n{res['city']}, {res['state']} {res['zipcode']}-{res['plus4'] or '0000'}"
    st.text_area("Suggested/Corrected Address", formatted_address, height=100)
