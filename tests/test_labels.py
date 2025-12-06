from pourover import Report
from pourover.core import Image, Table, FigureBlock, InteractiveFigure


def test_label_references_markdown():
    rpt = Report("Label Demo")
    sec = rpt.add_section("Figures & Tables")
    sec.add_image(Image("figure.png", caption="A sample figure"), label="fig:sample", numbered=True)
    tbl = Table(headers=["A"], rows=[[1]])
    sec.add_table(tbl, caption="Single value", label="tab:one", numbered=True)

    md = rpt.to_markdown()
    assert "**Figure 1:**" in md
    assert "*Table 1:*" in md
    assert rpt.ref("fig:sample") == "Figure 1"
    assert rpt.ref("tab:one") == "Table 1"


def test_interactive_figure_labels():
    rpt = Report("Interactive Labels")
    sec = rpt.add_section("Interactive")
    fig_block = FigureBlock(image=Image("plot.png", caption="Interactive figure"), label="fig:int", numbered=True)
    sec.blocks.append(InteractiveFigure(figure=fig_block, plotly_figure=None))

    rpt.to_markdown()
    assert rpt.ref("fig:int") == "Figure 1"
