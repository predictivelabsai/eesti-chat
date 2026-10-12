import argparse

from mcp_server.server import run

p = argparse.ArgumentParser(prog="python -m mcp_server")
p.add_argument("--transport", choices=["http", "stdio"], default="http")
run(p.parse_args().transport)
