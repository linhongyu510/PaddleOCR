from importlib.resources import files


def test_web_interface_is_packaged_with_polyocr() -> None:
    web_root = files("polyocr").joinpath("web")

    assert web_root.joinpath("index.html").is_file()
    assert web_root.joinpath("translation.html").is_file()
