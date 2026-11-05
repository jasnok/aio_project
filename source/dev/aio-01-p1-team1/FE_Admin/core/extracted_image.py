class _UploadedImage:
    """공고에서 꺼낸 사진을 업로드 함수가 받는 모양으로 맞춥니다.

    화면에서 고른 파일(st.file_uploader가 주는 값)과 같은 자리를 갖도록
    name, type, getvalue()만 흉내 냅니다. 그래야 사진을 올리는 코드를
    수동 등록과 똑같이 쓸 수 있습니다.
    """

    def __init__(self, image: dict):
        self.name = image["name"]
        self._data = image["data"]
        suffix = self.name.rsplit(".", 1)[-1].lower() if "." in self.name else "png"
        fallback_type = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
        self.type = image.get("mime_type") or fallback_type

    def getvalue(self) -> bytes:
        return self._data


