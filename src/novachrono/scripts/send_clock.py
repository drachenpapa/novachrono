import json
from datetime import datetime
from zoneinfo import ZoneInfo

from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
)
from novachrono.widgets.clock import render_clock_panel

CLOCK_PANEL_INDEX = 2


def main() -> None:
    host = ""
    local_token = ""

    client = TimesGateClient(
        TimesGateConfig(
            host=host,
            local_token=local_token,
        )
    )

    now = datetime.now(ZoneInfo("Europe/Berlin"))

    clock_panel = render_clock_panel(now)

    print(f"Sending clock to display {CLOCK_PANEL_INDEX + 1} ...")

    response = client.send_image(
        panel_index=CLOCK_PANEL_INDEX,
        image=clock_panel,
    )

    print("Response:")
    print(
        json.dumps(
            response,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
