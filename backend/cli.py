"""
OGI CLI
Usage:
    python cli.py run-transform --graph-id <id> --entity-id <id> --transform dns_resolve
    python cli.py list-transforms
    python cli.py create-graph --name "My Investigation"
"""
import asyncio
import json
import typer
import aiosqlite
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="ogi", help="OGI - Open Graph Intelligence CLI")
console = Console()
DB_PATH = Path("ogi.db")


async def _get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


@app.command("list-transforms")
def list_transforms():
    """List all available transforms."""
    from transform_engine import registry
    table = Table(title="Available Transforms")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name")
    table.add_column("Input Types")
    table.add_column("Requires Key")
    for t in registry.list_all():
        table.add_row(
            t.name,
            t.display_name,
            ", ".join(et.value for et in t.input_types),
            "✓" if t.requires_api_key else "",
        )
    console.print(table)


@app.command("create-graph")
def create_graph(
    name: str = typer.Option(..., help="Graph name"),
    description: str = typer.Option("", help="Graph description"),
):
    """Create a new graph."""
    async def _run():
        from database import init_db, db_create_graph
        import uuid
        await init_db()
        db = await _get_db()
        graph_id = str(uuid.uuid4())
        row = await db_create_graph(db, graph_id, name, description or None)
        await db.close()
        console.print(f"[green]Created graph:[/green] {row['id']} - {name}")

    asyncio.run(_run())


@app.command("list-graphs")
def list_graphs():
    """List all graphs."""
    async def _run():
        from database import init_db, db_get_graphs
        await init_db()
        db = await _get_db()
        rows = await db_get_graphs(db)
        await db.close()
        table = Table(title="Graphs")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Entities", justify="right")
        table.add_column("Edges", justify="right")
        for r in rows:
            table.add_row(r["id"][:8] + "...", r["name"],
                          str(r["entity_count"]), str(r["edge_count"]))
        console.print(table)

    asyncio.run(_run())


@app.command("run-transform")
def run_transform(
    graph_id: str = typer.Option(..., help="Graph ID"),
    entity_id: str = typer.Option(..., help="Entity ID"),
    transform: str = typer.Option(..., help="Transform name"),
    options: str = typer.Option("{}", help="JSON options dict"),
):
    """Run a transform on an entity."""
    async def _run():
        from database import init_db, db_get_entity, db_get_api_key, db_create_entity, db_create_edge
        from transform_engine import registry
        await init_db()
        db = await _get_db()

        entity = await db_get_entity(db, entity_id)
        if not entity:
            console.print(f"[red]Entity {entity_id} not found[/red]")
            return

        api_keys = {}
        for name in ["SHODAN_API_KEY", "VIRUSTOTAL_API_KEY", "HUNTER_API_KEY"]:
            val = await db_get_api_key(db, name)
            if val:
                api_keys[name] = val

        opts = json.loads(options)
        result = await registry.run(transform, entity, opts, api_keys)

        if result.success:
            console.print(f"[green]Transform succeeded:[/green] {len(result.entities)} entities, {len(result.edges)} edges")
            for msg in result.messages:
                console.print(f"  • {msg}")
            for e in result.entities:
                await db_create_entity(db, graph_id, e.dict())
            for edge in result.edges:
                await db_create_edge(db, graph_id, edge.dict())
        else:
            console.print(f"[red]Transform failed:[/red] {result.error}")

        await db.close()

    asyncio.run(_run())


@app.command("add-entity")
def add_entity(
    graph_id: str = typer.Option(..., help="Graph ID"),
    type_: str = typer.Option(..., "--type", help="Entity type (e.g. Domain, IPAddress)"),
    value: str = typer.Option(..., help="Entity value"),
    label: str = typer.Option("", help="Optional label"),
):
    """Add an entity to a graph."""
    async def _run():
        from database import init_db, db_create_entity
        from models import EntityType, Entity
        import uuid
        await init_db()
        db = await _get_db()
        entity = Entity(
            id=str(uuid.uuid4()),
            type=EntityType(type_),
            value=value,
            label=label or value,
        )
        await db_create_entity(db, graph_id, entity.dict())
        await db.close()
        console.print(f"[green]Added:[/green] {entity.id[:8]}... [{entity.type.value}] {value}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
