"""Blueprint palette for Unfold's built-in light, dark and system modes."""


def rgb(value):
    return " ".join(str(int(value[i : i + 2], 16)) for i in (1, 3, 5))


ADMIN_COLORS = {
    "primary": dict(
        zip(
            ("50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950"),
            map(
                rgb,
                (
                    "#F5F8FB",
                    "#EAF4FB",
                    "#C5D8E8",
                    "#7FB2E8",
                    "#FF4D2E",
                    "#FF4D2E",
                    "#C9341A",
                    "#C9341A",
                    "#123C6B",
                    "#0B2545",
                    "#0B2545",
                ),
            ),
            strict=True,
        )
    ),
    "base": dict(
        zip(
            ("50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950"),
            map(
                rgb,
                (
                    "#F5F8FB",
                    "#EAF4FB",
                    "#D8E2EC",
                    "#C5D8E8",
                    "#7D93AC",
                    "#5A7490",
                    "#2E4A68",
                    "#1C4578",
                    "#123C6B",
                    "#0B2545",
                    "#0B2545",
                ),
            ),
            strict=True,
        )
    ),
    "font": {
        "subtle-light": rgb("#5A7490"),
        "subtle-dark": rgb("#7D93AC"),
        "default-light": rgb("#2E4A68"),
        "default-dark": rgb("#C5D8E8"),
        "important-light": rgb("#0B2545"),
        "important-dark": rgb("#EAF4FB"),
    },
}
