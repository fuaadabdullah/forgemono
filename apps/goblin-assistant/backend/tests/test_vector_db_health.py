import os
import pathlib
import tempfile


def test_chroma_db_path_exists():
    """Test that the ChromaDB path points to an existing location."""
    # Set the environment variable to the new consolidated path
    chroma_path = "/Users/fuaadabdullah/ForgeMonorepo/data/vector/chroma/chroma.sqlite3"
    os.environ["CHROMA_DB_PATH"] = chroma_path

    # Check that the path is set correctly
    assert os.getenv("CHROMA_DB_PATH") == chroma_path

    # Check that the directory exists
    chroma_dir = pathlib.Path(chroma_path).parent
    assert chroma_dir.exists(), f"ChromaDB directory {chroma_dir} should exist"

    print(f"✓ ChromaDB path verified: {chroma_path}")


def test_chroma_db_file_operations():
    """Test basic file operations on the ChromaDB path."""
    chroma_path = "/Users/fuaadabdullah/ForgeMonorepo/data/vector/chroma/chroma.sqlite3"
    chroma_dir = pathlib.Path(chroma_path).parent

    # Test that we can create a temporary file in the directory
    with tempfile.NamedTemporaryFile(
        dir=chroma_dir, suffix=".tmp", delete=False
    ) as tmp_file:
        tmp_file.write(b"test data")
        tmp_path = tmp_file.name

    # Verify the file was created
    assert pathlib.Path(tmp_path).exists()

    # Clean up
    pathlib.Path(tmp_path).unlink()

    print(f"✓ File operations work in ChromaDB directory: {chroma_dir}")


def test_vector_data_structure():
    """Test that the vector data structure is properly organized."""
    data_dir = pathlib.Path("/Users/fuaadabdullah/ForgeMonorepo/data")
    vector_dir = data_dir / "vector"
    chroma_dir = vector_dir / "chroma"

    # Check directory structure
    assert data_dir.exists()
    assert vector_dir.exists()
    assert chroma_dir.exists()

    # Check that chroma.sqlite3 file exists (or can be created)
    chroma_file = chroma_dir / "chroma.sqlite3"
    if chroma_file.exists():
        print(f"✓ ChromaDB file exists: {chroma_file}")
    else:
        print(f"✓ ChromaDB directory ready for file creation: {chroma_dir}")

    print("✓ Vector data structure verified")
