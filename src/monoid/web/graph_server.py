"""HTTP server for serving interactive graph visualizations."""
import http.server
import json
import socketserver
import webbrowser
from pathlib import Path
from typing import Any
import threading
from monoid.metadata.graph import graph_manager


class GraphHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for graph visualization."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.directory = str(Path(__file__).parent / "templates")
        super().__init__(*args, directory=self.directory, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/api/graph":
            self.send_graph_data()
        elif self.path == "/" or self.path == "/index.html":
            self.path = "/graph.html"
            super().do_GET()
        else:
            super().do_GET()

    def send_graph_data(self) -> None:
        """Send graph data as JSON."""
        try:
            g = graph_manager.build_graph()

            nodes = []
            for node_id in g.nodes():
                node_data = g.nodes[node_id]
                nodes.append({
                    "id": node_id,
                    "title": node_data.get("title", "Untitled"),
                    "type": node_data.get("type", "note"),
                    "tags": [tag.name if hasattr(tag, 'name') else str(tag)
                            for tag in node_data.get("tags", [])],
                    "degree": g.degree(node_id)
                })

            edges = []
            for source, target, data in g.edges(data=True):
                edges.append({
                    "source": source,
                    "target": target,
                    "type": data.get("type", "unknown"),
                    "weight": data.get("weight", 1.0)
                })

            graph_data = {"nodes": nodes, "edges": edges}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(graph_data).encode())

        except Exception as e:
            self.send_error(500, f"Error building graph: {str(e)}")

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass


def start_server(port: int = 8765, open_browser: bool = True) -> None:
    """Start the web server for graph visualization."""
    handler = GraphHandler

    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/graph.html"
        print(f"Starting web server at {url}")

        if open_browser:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()

        print("Press Ctrl+C to stop the server")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
