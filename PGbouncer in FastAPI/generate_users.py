#!/usr/bin/env python3
"""
Generate 10,000 fake users using Faker and save to PostgreSQL database.

Requirements:
- pip install sqlalchemy psycopg2-binary faker python-dotenv

Environment variables (create a .env file):
- DB_HOST=localhost
- DB_PORT=5432
- DB_NAME=your_database
- DB_USER=your_username
- DB_PASSWORD=your_password
"""

import os
import sys
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from faker import Faker
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Construct DATABASE_URL
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# SQLAlchemy setup
Base = declarative_base()

class User(Base):
    """User model matching the required structure."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(127), unique=True, nullable=False, index=True)
    first_name = Column(String(127), nullable=False)
    last_name = Column(String(127), nullable=False)
    role = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<User(username='{self.username}', name='{self.first_name} {self.last_name}', role={self.role})>"

def create_database_connection():
    """Create database engine and session."""
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=True  # Set to True for SQL debugging
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        print(f"✅ Connected to PostgreSQL database: {DB_CONFIG['database']}")
        return engine
    
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("\nPlease check your database configuration:")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        sys.exit(1)

def create_tables(engine):
    """Create database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        sys.exit(1)

def generate_fake_users(n: int, fake: Faker) -> List[dict]:
    """Generate n fake users with unique usernames."""
    users = []
    usernames = set()
    
    print(f"🔄 Generating {n:,} fake users...")
    
    attempts = 0
    max_attempts = n * 2  # Allow some room for duplicates
    
    while len(users) < n and attempts < max_attempts:
        username = fake.user_name()
        
        # Ensure unique usernames
        if username not in usernames:
            user_data = {
                'username': username,
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'role': fake.random_int(min=1, max=3)
            }
            users.append(user_data)
            usernames.add(username)
        
        attempts += 1
        
        if attempts % 1000 == 0:
            print(f"   Generated {len(users):,}/{n:,} users...")
    
    if len(users) < n:
        print(f"⚠️  Warning: Only generated {len(users):,} unique users out of {n:,} requested")
    
    return users

def batch_insert_users(session: Session, users_data: List[dict], batch_size: int = 1000) -> int:
    """Insert users in batches for better performance."""
    total_inserted = 0
    total_batches = (len(users_data) + batch_size - 1) // batch_size
    
    print(f"🔄 Inserting users in batches of {batch_size:,}...")
    
    for i in range(0, len(users_data), batch_size):
        batch = users_data[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            # Create User objects for this batch
            user_objects = [User(**user_data) for user_data in batch]
            
            # Add batch to session
            session.add_all(user_objects)
            session.commit()
            
            total_inserted += len(batch)
            print(f"   Batch {batch_num}/{total_batches}: Inserted {len(batch):,} users (Total: {total_inserted:,})")
            
        except IntegrityError as e:
            session.rollback()
            print(f"   Batch {batch_num}/{total_batches}: Integrity error (likely duplicate usernames)")
            
            # Try inserting one by one for this batch
            individual_inserted = insert_users_individually(session, batch)
            total_inserted += individual_inserted
            
        except Exception as e:
            session.rollback()
            print(f"   Batch {batch_num}/{total_batches}: Error - {e}")
    
    return total_inserted

def insert_users_individually(session: Session, users_data: List[dict]) -> int:
    """Insert users one by one, skipping duplicates."""
    inserted = 0
    
    for user_data in users_data:
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            inserted += 1
        except IntegrityError:
            session.rollback()
            # Skip duplicate username
            continue
        except Exception as e:
            session.rollback()
            print(f"     Error inserting user {user_data['username']}: {e}")
    
    return inserted

def verify_data(session: Session) -> None:
    """Verify the inserted data."""
    try:
        total_users = session.query(User).count()
        
        # Get role distribution
        role_counts = {}
        for role in [1, 2, 3]:
            count = session.query(User).filter(User.role == role).count()
            role_counts[role] = count
        
        # Get sample users
        sample_users = session.query(User).limit(5).all()
        
        print(f"\n📊 Data verification:")
        print(f"   Total users in database: {total_users:,}")
        print(f"   Role distribution:")
        for role, count in role_counts.items():
            percentage = (count / total_users * 100) if total_users > 0 else 0
            print(f"     Role {role}: {count:,} users ({percentage:.1f}%)")
        
        print(f"\n👥 Sample users:")
        for user in sample_users:
            print(f"   {user}")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

def main():
    """Main function to generate and insert fake users."""
    print("🚀 Starting fake user generation...")
    start_time = time.time()
    
    # Configuration
    NUM_USERS = 10_000
    BATCH_SIZE = 1_000
    
    # Initialize Faker
    fake = Faker()
    fake.seed_instance(42)  # For reproducible results
    
    # Create database connection
    engine = create_database_connection()
    
    # Create tables
    create_tables(engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Generate fake users
        users_data = generate_fake_users(NUM_USERS, fake)
        
        # Insert users into database
        inserted_count = batch_insert_users(session, users_data, BATCH_SIZE)
        
        # Verify data
        verify_data(session)
        
        # Calculate execution time
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n✅ Successfully completed!")
        print(f"   Users inserted: {inserted_count:,}")
        print(f"   Execution time: {execution_time:.2f} seconds")
        print(f"   Average rate: {inserted_count/execution_time:.0f} users/second")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        session.rollback()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        session.rollback()
    finally:
        session.close()
        engine.dispose()
        print("\n🔚 Database connection closed")

if __name__ == "__main__":
    main()

