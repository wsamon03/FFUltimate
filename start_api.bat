@echo off
set MOCK_ESPN=false
pushd C:UsersqabctDocumentsProgrammingFantasyFootballVersion2
uvicorn ingest.service.app:app --host 0.0.0.0 --port 8002 --log-level info
popd
