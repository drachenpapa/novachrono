from pathlib import Path

from novachrono.dashboard import render_dashboard
from novachrono.preview import create_preview, save_preview


def main() -> None:
    panels = render_dashboard()
    preview = create_preview(panels)

    destination = Path("output/dashboard-preview.png")
    save_preview(preview, destination)

    print(f"Dashboard preview written to {destination}")


if __name__ == "__main__":
    main()
