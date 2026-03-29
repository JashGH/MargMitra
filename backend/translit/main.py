from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="Transliteration Service")


class TransRequest(BaseModel):
    text: str
    target_lang: str = "hi"


@app.post("/transliterate")
def transliterate(request: TransRequest):
    try:
        # Google Input Tools transliteration API.
        url = "https://inputtools.google.com/request"
        params = {
            "text": request.text.strip(),
            "ime": "transliteration_en_" + request.target_lang,
            "num": 1,
            "cp": 0,
            "cs": 1,
            "ie": "utf-8",
            "oe": "utf-8",
            "app": "demopage",
        }
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        output = request.text  # Fallback
        # Expected shape: ["SUCCESS", [[<input>, [<candidate1>, ...]]]]
        if (
            isinstance(data, list)
            and len(data) > 1
            and data[0] == "SUCCESS"
            and isinstance(data[1], list)
            and len(data[1]) > 0
            and isinstance(data[1][0], list)
            and len(data[1][0]) > 1
            and isinstance(data[1][0][1], list)
            and len(data[1][0][1]) > 0
            and isinstance(data[1][0][1][0], str)
        ):
            output = data[1][0][1][0]

        return {"output": output, "lang": request.target_lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
