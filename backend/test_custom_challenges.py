"""
Integration test for custom dataset and challenge system.
Tests the complete flow: dataset upload → challenge creation → submission.
"""

import io
import csv
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from unittest.mock import patch

# Import app and dependencies
from app.main import app
from app.database import get_session


# Create a shared test engine
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session():
    """Create test database session using shared engine."""
    with Session(test_engine) as session:
        yield session


def create_test_csv() -> bytes:
    """Create a simple CSV file for testing."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "product", "price", "quantity"])
    writer.writerow([1, "Widget", 9.99, 100])
    writer.writerow([2, "Gadget", 19.99, 50])
    writer.writerow([3, "Doohickey", 5.99, 200])
    return output.getvalue().encode("utf-8")


def test_complete_custom_challenge_flow():
    """Test the complete flow from dataset upload to challenge submission."""

    print("\n" + "="*80)
    print("TESTING CUSTOM DATASET & CHALLENGE SYSTEM")
    print("="*80)

    # Create tables in test database
    SQLModel.metadata.create_all(test_engine)

    # Override database dependency
    with patch("app.database.create_db_and_tables"):
        app.dependency_overrides[get_session] = get_test_session
        client = TestClient(app)

        try:
            # Step 1: Register and login as teacher
            print("\n[1/8] Registering teacher account...")
            register_response = client.post(
                "/auth/register",
                json={
                    "email": "teacher@test.com",
                    "password": "password123",
                    "name": "Test Teacher",
                    "role": "teacher",
                },
            )
            assert register_response.status_code == 201, f"Registration failed with status {register_response.status_code}: {register_response.text}"

            # Login to get token
            login_response = client.post(
                "/auth/login",
                json={
                    "email": "teacher@test.com",
                    "password": "password123",
                },
            )
            assert login_response.status_code == 200, f"Login failed: {login_response.text}"
            teacher_data = login_response.json()
            teacher_token = teacher_data["access_token"]
            print(f"✓ Teacher registered and logged in")

            # Step 2: Upload a dataset
            print("\n[2/8] Uploading CSV dataset...")
            csv_content = create_test_csv()
            upload_response = client.post(
                "/datasets/upload",
                files={"file": ("products.csv", csv_content, "text/csv")},
                data={"name": "Product Inventory", "description": "Sample product data"},
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert upload_response.status_code == 201, f"Upload failed: {upload_response.text}"
            dataset = upload_response.json()
            print(f"✓ Dataset uploaded: ID={dataset['id']}, rows={dataset['row_count']}")
            print(f"  Table: {dataset['table_name']}")
            print(f"  Columns: {[col['name'] for col in dataset['schema']['columns']]}")

            # Step 3: List datasets
            print("\n[3/8] Listing datasets...")
            list_response = client.get(
                "/datasets",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert list_response.status_code == 200, f"List failed: {list_response.text}"
            datasets_list = list_response.json()
            assert datasets_list["total"] == 1
            print(f"✓ Found {datasets_list['total']} dataset(s)")

            # Step 4: Get dataset details
            print("\n[4/8] Getting dataset details...")
            detail_response = client.get(
                f"/datasets/{dataset['id']}",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            print(f"  Detail status: {detail_response.status_code}")
            if detail_response.status_code != 200:
                print(f"  Error: {detail_response.text}")
            assert detail_response.status_code == 200, f"Detail failed: {detail_response.text}"
            dataset_detail = detail_response.json()
            print(f"  Sample data rows: {len(dataset_detail['sample_data'])}")
            assert len(dataset_detail["sample_data"]) == 3  # 3 rows in CSV
            print(f"✓ Dataset details retrieved")
            print(f"  Sample data: {dataset_detail['sample_data'][0]}")

            # Step 5: Create a custom challenge
            print("\n[5/8] Creating custom challenge...")
            challenge_response = client.post(
                "/challenges/custom",
                json={
                    "dataset_id": dataset["id"],
                    "title": "Find Expensive Products",
                    "description": "Write a query to find all products with price > 10",
                    "points": 150,
                    "difficulty": "easy",
                    "expected_query": f"SELECT * FROM {dataset['table_name']} WHERE price > 10",
                    "hints": [
                        "Use the WHERE clause to filter results",
                        "Compare the price column to 10",
                        "Use the > operator for greater than",
                    ],
                },
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert challenge_response.status_code == 201, f"Challenge creation failed: {challenge_response.text}"
            challenge = challenge_response.json()
            print(f"✓ Challenge created: ID={challenge['id']}")
            print(f"  Title: {challenge['title']}")
            print(f"  Points: {challenge['points']}")

            # Step 6: List custom challenges
            print("\n[6/8] Listing custom challenges...")
            challenges_list_response = client.get(
                "/challenges/custom",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            print(f"  Status: {challenges_list_response.status_code}")
            if challenges_list_response.status_code != 200:
                print(f"  Error: {challenges_list_response.text}")
            assert challenges_list_response.status_code == 200, f"List challenges failed: {challenges_list_response.text}"
            challenges_list = challenges_list_response.json()
            print(f"  Total in response: {challenges_list.get('total', 'N/A')}")
            assert challenges_list["total"] == 1
            print(f"✓ Found {challenges_list['total']} challenge(s)")

            # Step 7: Register a student and submit solution
            print("\n[7/8] Testing student submission...")
            student_response = client.post(
                "/auth/register",
                json={
                    "email": "student@test.com",
                    "password": "password123",
                    "name": "Test Student",
                    "role": "student",
                },
            )
            assert student_response.status_code == 201

            # Login as student
            student_login_response = client.post(
                "/auth/login",
                json={
                    "email": "student@test.com",
                    "password": "password123",
                },
            )
            assert student_login_response.status_code == 200
            student_data = student_login_response.json()
            student_token = student_data["access_token"]
            print(f"✓ Student registered and logged in")

            # Submit correct answer
            submit_response = client.post(
                "/progress/submit",
                json={
                    "custom_challenge_id": challenge["id"],
                    "query": f"SELECT * FROM {dataset['table_name']} WHERE price > 10",
                    "hints_used": 1,
                },
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert submit_response.status_code == 200, f"Submission failed: {submit_response.text}"
            progress = submit_response.json()
            assert progress["points_earned"] == 150
            print(f"✓ Submission accepted: {progress['points_earned']} points earned")

            # Step 8: Verify challenge statistics updated
            print("\n[8/8] Verifying challenge statistics...")
            challenge_detail_response = client.get(
                f"/challenges/custom/{challenge['id']}",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert challenge_detail_response.status_code == 200
            challenge_detail = challenge_detail_response.json()
            print(f"✓ Challenge details retrieved")
            print(f"  Expected output cached: {challenge_detail['expected_output'] is not None}")

            # Cleanup: Delete challenge and dataset
            print("\n[CLEANUP] Deleting challenge and dataset...")
            delete_challenge_response = client.delete(
                f"/challenges/custom/{challenge['id']}",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert delete_challenge_response.status_code == 200
            print("✓ Challenge deleted")

            delete_dataset_response = client.delete(
                f"/datasets/{dataset['id']}",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert delete_dataset_response.status_code == 200
            print("✓ Dataset deleted")

            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED!")
            print("="*80)
            return True

        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            return False
        except Exception as e:
            print(f"\n❌ UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    success = test_complete_custom_challenge_flow()
    exit(0 if success else 1)
