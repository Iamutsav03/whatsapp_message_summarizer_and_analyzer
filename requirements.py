import altair as alt


def month_line_chart(df):
    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("MONTH:N", sort=month_order, title="Month"),
            y=alt.Y("COUNT:Q", title="Activity Count"),
            tooltip=["MONTH", "COUNT"],
        )
        .properties(height=300)
    )
    return chart


def dayname_bar_chart(df):
    order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("DAY NAME:N", sort=order, title="Day"),
            y=alt.Y("COUNT:Q", title="Activity Count"),
            tooltip=["DAY NAME", "COUNT"],
        )
        .properties(height=300)
    )
    return chart


def year_hbar_chart(df):
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y("YEAR:N", sort="-x", title="Year"),
            x=alt.X("COUNT:Q", title="Activity Count"),
            tooltip=["YEAR", "COUNT"],
        )
        .properties(height=300)
    )
    return chart
