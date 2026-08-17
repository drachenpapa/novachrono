from novachrono.i18n import translate


def test_translate_returns_german_weather_title() -> None:
    assert translate("weather.title", locale="de_DE") == "WETTER"


def test_translate_returns_english_weather_title() -> None:
    assert translate("weather.title", locale="en_US") == "WEATHER"


def test_translate_returns_key_for_unknown_translation() -> None:
    assert translate("something.unknown", locale="de_DE") == "something.unknown"


def test_translate_falls_back_to_default_locale() -> None:
    assert translate("weather.title", locale="unsupported") == "WETTER"
