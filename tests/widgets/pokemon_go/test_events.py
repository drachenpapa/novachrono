from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

from novachrono.design import PANEL_SIZE
from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoEventType,
    PokemonGoFeaturedPokemon,
)
from novachrono.widgets.pokemon_go.events import (
    EVENT_FRAME_DURATION_MS,
    render_event_animation,
    render_event_panel,
)

BERLIN = ZoneInfo("Europe/Berlin")


def _create_event(
    *,
    event_type: PokemonGoEventType,
    name: str,
    pokemon: tuple[PokemonGoFeaturedPokemon, ...] = (),
    start_hour: int = 14,
    end_hour: int = 17,
    day: int = 10,
    bonus: str | None = None,
) -> PokemonGoEvent:
    return PokemonGoEvent(
        event_type=event_type,
        name=name,
        start=datetime(
            2026,
            10,
            day,
            start_hour,
            tzinfo=BERLIN,
        ),
        end=datetime(
            2026,
            10,
            day,
            end_hour,
            tzinfo=BERLIN,
        ),
        featured_pokemon=pokemon,
        bonus=bonus,
    )


def _artwork(
    color: str,
) -> Image.Image:
    return Image.new(
        mode="RGBA",
        size=(20, 20),
        color=color,
    )


def test_event_frame_duration_is_30_seconds() -> None:
    assert EVENT_FRAME_DURATION_MS == 30_000


def test_render_event_panel_has_expected_size_and_mode() -> None:
    panel = render_event_panel(
        EventSchedule(),
        locale="de_DE",
    )

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
    assert panel.mode == "RGB"


def test_render_event_panel_is_deterministic() -> None:
    schedule = EventSchedule(
        community_day=_create_event(
            event_type=PokemonGoEventType.COMMUNITY_DAY,
            name="Community Day",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="Zorua",
                ),
            ),
        )
    )

    first = render_event_panel(
        schedule,
        locale="de_DE",
    )

    second = render_event_panel(
        schedule,
        locale="de_DE",
    )

    assert first.tobytes() == second.tobytes()


def test_render_event_animation_uses_fixed_category_order() -> None:
    schedule = EventSchedule(
        community_day=_create_event(
            event_type=PokemonGoEventType.COMMUNITY_DAY,
            name="Community Day",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="A",
                    artwork_url="cd",
                ),
            ),
        ),
        community_day_classic=_create_event(
            event_type=PokemonGoEventType.COMMUNITY_DAY_CLASSIC,
            name="Community Day Classic",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="B",
                    artwork_url="classic",
                ),
            ),
        ),
        spotlight_hour=_create_event(
            event_type=PokemonGoEventType.SPOTLIGHT_HOUR,
            name="Spotlight Hour",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="C",
                    artwork_url="spotlight",
                ),
            ),
        ),
        max_monday=_create_event(
            event_type=PokemonGoEventType.MAX_MONDAY,
            name="Max Monday",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="D",
                    artwork_url="max",
                ),
            ),
        ),
    )

    frames = render_event_animation(
        schedule,
        locale="de_DE",
        artwork_by_url={
            "cd": _artwork("#FF0000"),
            "classic": _artwork("#00FF00"),
            "spotlight": _artwork("#0000FF"),
            "max": _artwork("#FF00FF"),
        },
    )

    assert len(frames) == 4

    assert (255, 0, 0) in set(frames[0].get_flattened_data())
    assert (0, 255, 0) in set(frames[1].get_flattened_data())
    assert (0, 0, 255) in set(frames[2].get_flattened_data())
    assert (255, 0, 255) in set(frames[3].get_flattened_data())


def test_render_event_animation_creates_one_frame_per_featured_pokemon() -> None:
    schedule = EventSchedule(
        community_day=_create_event(
            event_type=PokemonGoEventType.COMMUNITY_DAY,
            name="Community Day",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="Sandshrew",
                    artwork_url="normal",
                ),
                PokemonGoFeaturedPokemon(
                    name="Alola-Sandshrew",
                    artwork_url="alola",
                ),
            ),
        ),
        max_monday=_create_event(
            event_type=PokemonGoEventType.MAX_MONDAY,
            name="Max Monday",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="Articuno",
                ),
                PokemonGoFeaturedPokemon(
                    name="Zapdos",
                ),
                PokemonGoFeaturedPokemon(
                    name="Moltres",
                ),
            ),
        ),
    )

    frames = render_event_animation(
        schedule,
        locale="de_DE",
        artwork_by_url={
            "normal": _artwork("#FF0000"),
            "alola": _artwork("#0000FF"),
        },
    )

    assert len(frames) == 5
    assert frames[0].tobytes() != frames[1].tobytes()


def test_render_event_animation_omits_missing_categories() -> None:
    schedule = EventSchedule(
        max_monday=_create_event(
            event_type=PokemonGoEventType.MAX_MONDAY,
            name="Max Monday",
            pokemon=(PokemonGoFeaturedPokemon(name="Sobble"),),
        )
    )

    frames = render_event_animation(
        schedule,
        locale="de_DE",
    )

    assert len(frames) == 1


def test_render_event_animation_empty_schedule_returns_single_frame() -> None:
    frames = render_event_animation(
        EventSchedule(),
        locale="de_DE",
    )

    assert len(frames) == 1
    assert frames[0].size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
    assert frames[0].mode == "RGB"


def test_render_event_panel_uses_provided_artwork() -> None:
    artwork_url = "https://example.com/zorua.png"

    schedule = EventSchedule(
        community_day=_create_event(
            event_type=PokemonGoEventType.COMMUNITY_DAY,
            name="Community Day",
            pokemon=(
                PokemonGoFeaturedPokemon(
                    name="Zorua",
                    artwork_url=artwork_url,
                ),
            ),
        )
    )

    panel_with_artwork = render_event_panel(
        schedule,
        locale="de_DE",
        artwork_by_url={
            artwork_url: _artwork("#FF00FF"),
        },
    )

    panel_without_artwork = render_event_panel(
        schedule,
        locale="de_DE",
    )

    assert panel_with_artwork.tobytes() != panel_without_artwork.tobytes()
    assert (255, 0, 255) in set(panel_with_artwork.get_flattened_data())


def test_render_event_panel_changes_with_locale() -> None:
    event = _create_event(
        event_type=PokemonGoEventType.COMMUNITY_DAY,
        name="Community Day",
        pokemon=(PokemonGoFeaturedPokemon(name="Sobble"),),
    )

    german = render_event_panel(
        EventSchedule(community_day=event),
        locale="de_DE",
    )

    english = render_event_panel(
        EventSchedule(community_day=event),
        locale="en_US",
    )

    assert german.tobytes() != english.tobytes()


def test_max_monday_ignores_event_hours() -> None:
    morning = _create_event(
        event_type=PokemonGoEventType.MAX_MONDAY,
        name="Max Monday",
        pokemon=(PokemonGoFeaturedPokemon(name="Sobble"),),
        start_hour=6,
        end_hour=21,
    )

    evening = _create_event(
        event_type=PokemonGoEventType.MAX_MONDAY,
        name="Max Monday",
        pokemon=(PokemonGoFeaturedPokemon(name="Sobble"),),
        start_hour=18,
        end_hour=19,
    )

    morning_panel = render_event_panel(
        EventSchedule(max_monday=morning),
        locale="de_DE",
    )

    evening_panel = render_event_panel(
        EventSchedule(max_monday=evening),
        locale="de_DE",
    )

    assert morning_panel.tobytes() == evening_panel.tobytes()


def test_max_monday_changes_with_date() -> None:
    first_event = _create_event(
        event_type=PokemonGoEventType.MAX_MONDAY,
        name="Max Monday",
        pokemon=(PokemonGoFeaturedPokemon(name="Sobble"),),
        day=5,
    )

    second_event = _create_event(
        event_type=PokemonGoEventType.MAX_MONDAY,
        name="Max Monday",
        pokemon=(PokemonGoFeaturedPokemon(name="Sobble"),),
        day=12,
    )

    first_panel = render_event_panel(
        EventSchedule(max_monday=first_event),
        locale="de_DE",
    )

    second_panel = render_event_panel(
        EventSchedule(max_monday=second_event),
        locale="de_DE",
    )

    assert first_panel.tobytes() != second_panel.tobytes()


def test_render_event_panel_handles_event_without_featured_pokemon() -> None:
    panel = render_event_panel(
        EventSchedule(
            community_day=_create_event(
                event_type=PokemonGoEventType.COMMUNITY_DAY,
                name="Community Day",
                bonus="3\u00d7 Catch XP",
            )
        ),
        locale="de_DE",
    )

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
    assert panel.mode == "RGB"
