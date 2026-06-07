import uvicorn

if __name__ == "__main__":
    uvicorn.run("user_api.app:app", host="0.0.0.0", port=8001, reload=False)
