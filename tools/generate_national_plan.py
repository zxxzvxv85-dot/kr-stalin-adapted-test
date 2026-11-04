"""Single composed generator; preserves the provisional industrial GUI."""
from generate_provisional_industry_gui import render,ROOT
from generation_io import cli
if __name__=='__main__':cli(render,root=ROOT)
