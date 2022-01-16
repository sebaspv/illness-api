import json
from fastapi import FastAPI
import requests
from dotenv import dotenv_values
import uvicorn
import wikipediaapi

config = dotenv_values(".env")
headers = {
    "App-Id": config["INFERMEDICA_ID"],
    "App-Key": config["INFERMEDICA_KEY"],
    "Content-Type": "application/json",
}
sex_list = {"male", "female"}
app = FastAPI()
wiki = wikipediaapi.Wikipedia(language="en")


@app.post("/get_illness")
async def get_symptoms(prompt: str, sex: str, age: int) -> dict:
    if sex not in sex_list:
        sex = "male"
    data = {"text": prompt, "age": {"value": age}}
    symptoms = requests.post(
        config["API_URL"] + "parse", headers=headers, data=json.dumps(data)
    )
    symptoms_content = json.loads(symptoms.text)["mentions"]
    for symptom in symptoms_content:
        symptom.pop("name")
        symptom.pop("common_name")
        symptom.pop("type")
        symptom.pop("orth")
    data_illness = {"sex": sex, "age": {"value": age}, "evidence": symptoms_content}
    possible_illnesses_request = requests.post(
        config["API_URL"] + "diagnosis", headers=headers, data=json.dumps(data_illness)
    )
    possible_specialist = requests.post(
        config["API_URL"] + "recommend_specialist", headers=headers, data=json.dumps(data_illness)
    )
    specialist = json.loads(possible_specialist.text)["recommended_specialist"]
    possible_symptoms_content = json.loads(symptoms.text)["mentions"]
    possible_illnesses = json.loads(possible_illnesses_request.text)["conditions"]
    possible_symptoms = possible_symptoms_content
    for illness in possible_illnesses:
        illness["description"] = wiki.page(illness["name"]).summary.split(".")[0]
        if illness["description"] == "":
            illness["description"] = "No info available"
    specialist["description"] = wiki.page(specialist["name"]).summary.split(".")[0]
    if specialist["description"] == "":
        specialist["description"] == "No info available"
    return {"illnesses": possible_illnesses, "symptoms": possible_symptoms, "emergency": json.loads(possible_illnesses_request.text)["has_emergency_evidence"], "specialist": specialist}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
