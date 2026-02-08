import os
import pathlib


def test_chroma_db_path():
    """Test that the ChromaDB path is correctly configured for the new data structure."""
    # Set the environment variable to the new consolidated path
    os.environ.setdefault(
        "CHROMA_DB_PATH",
        "/Users/fuaadabdullah/ForgeMonorepo/data/vector/chroma/chroma.sqlite3",
    )

    # Check that the environment variable is set
    chroma_path = os.getenv("CHROMA_DB_PATH")
    assert chroma_path is not None, "CHROMA_DB_PATH environment variable should be set"

    # Check that the path points to the expected location
    expected_path = (
        "/Users/fuaadabdullah/ForgeMonorepo/data/vector/chroma/chroma.sqlite3"
    )
    assert chroma_path == expected_path, (
        f"CHROMA_DB_PATH should be {expected_path}, got {chroma_path}"
    )

    # Check that the directory exists
    chroma_dir = pathlib.Path(chroma_path).parent
    assert chroma_dir.exists(), f"ChromaDB directory {chroma_dir} should exist"

    print(f"✓ ChromaDB path correctly configured: {chroma_path}")
    print(f"✓ Directory exists: {chroma_dir}")


def test_data_structure_consolidation():
    """Test that the data structure consolidation is working."""
    # Check that the main data directory exists
    data_dir = pathlib.Path("/Users/fuaadabdullah/ForgeMonorepo/data")
    assert data_dir.exists(), "Main data directory should exist"

    # Check that vector subdirectory exists
    vector_dir = data_dir / "vector"
    assert vector_dir.exists(), "Vector data directory should exist"

    # Check that chroma subdirectory exists
    chroma_dir = vector_dir / "chroma"
    assert chroma_dir.exists(), "Chroma data directory should exist"

    # Check that SQLite subdirectory exists
    sqlite_dir = data_dir / "sqlite"
    assert sqlite_dir.exists(), "SQLite data directory should exist"

    print("✓ Data structure consolidation verified:")
    print(f"  - Main data dir: {data_dir}")
    print(f"  - Vector dir: {vector_dir}")
    print(f"  - Chroma dir: {chroma_dir}")
    print(f"  - SQLite dir: {sqlite_dir}")
