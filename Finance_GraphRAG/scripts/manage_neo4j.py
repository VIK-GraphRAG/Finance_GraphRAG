#!/usr/bin/env python3
"""
Neo4j Database Management Script
Neo4j 데이터베이스를 관리하는 스크립트 (백업, 복원, 초기화, 통계)
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from neo4j import GraphDatabase

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

BACKUP_DIR = Path("./backups")
BACKUP_DIR.mkdir(exist_ok=True)


class Neo4jManager:
    """Neo4j 데이터베이스 관리 클래스"""
    
    def __init__(self, uri: str = NEO4J_URI, username: str = NEO4J_USERNAME, password: str = NEO4J_PASSWORD):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        
    def connect(self):
        """Neo4j 연결"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # 연결 테스트
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"✓ Connected to Neo4j: {self.uri}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        if self.driver:
            self.driver.close()
            print("✓ Connection closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        with self.driver.session() as session:
            # 노드 수
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            
            # 관계 수
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()["count"]
            
            # 노드 타입별 수
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            node_types = {record["label"]: record["count"] for record in result}
            
            # 관계 타입별 수
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            rel_types = {record["type"]: record["count"] for record in result}
            
            return {
                "total_nodes": node_count,
                "total_relationships": rel_count,
                "node_types": node_types,
                "relationship_types": rel_types,
                "timestamp": datetime.now().isoformat()
            }
    
    def print_stats(self):
        """통계 출력"""
        print("\n" + "="*70)
        print("Neo4j Database Statistics")
        print("="*70)
        
        stats = self.get_stats()
        
        print(f"\nOverview:")
        print(f"  Total Nodes: {stats['total_nodes']:,}")
        print(f"  Total Relationships: {stats['total_relationships']:,}")
        
        print(f"\nNode Types:")
        for label, count in stats['node_types'].items():
            print(f"  {label}: {count:,}")
        
        print(f"\nRelationship Types:")
        for rel_type, count in stats['relationship_types'].items():
            print(f"  {rel_type}: {count:,}")
        
        print(f"\nTimestamp: {stats['timestamp']}")
        print("="*70)
    
    def _convert_neo4j_types(self, obj):
        """Neo4j 타입을 JSON 직렬화 가능한 타입으로 변환"""
        from neo4j.time import DateTime, Date, Time
        
        if isinstance(obj, (DateTime, Date, Time)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._convert_neo4j_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_neo4j_types(item) for item in obj]
        else:
            return obj
    
    def export_to_json(self, output_file: str = None) -> str:
        """데이터베이스를 JSON으로 내보내기"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = BACKUP_DIR / f"neo4j_backup_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        print(f"\nExporting database to: {output_file}")
        
        with self.driver.session() as session:
            # 모든 노드 가져오기
            print("  Fetching nodes...")
            result = session.run("""
                MATCH (n)
                RETURN elementId(n) as id, labels(n) as labels, properties(n) as properties
            """)
            nodes = [self._convert_neo4j_types(dict(record)) for record in result]
            print(f"    {len(nodes)} nodes")
            
            # 모든 관계 가져오기
            print("  Fetching relationships...")
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN elementId(a) as source, elementId(b) as target, type(r) as type, properties(r) as properties
            """)
            relationships = [self._convert_neo4j_types(dict(record)) for record in result]
            print(f"    {len(relationships)} relationships")
        
        # JSON으로 저장
        backup_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "uri": self.uri,
                "node_count": len(nodes),
                "relationship_count": len(relationships)
            },
            "nodes": nodes,
            "relationships": relationships
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Export completed: {output_file}")
        return str(output_file)
    
    def import_from_json(self, input_file: str, clear_before: bool = False):
        """JSON에서 데이터베이스로 가져오기"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"✗ File not found: {input_file}")
            return
        
        print(f"\nImporting database from: {input_file}")
        
        # JSON 읽기
        with open(input_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        nodes = backup_data.get("nodes", [])
        relationships = backup_data.get("relationships", [])
        
        print(f"  Nodes to import: {len(nodes)}")
        print(f"  Relationships to import: {len(relationships)}")
        
        # 기존 데이터 삭제 (옵션)
        if clear_before:
            print("\n  Clearing existing data...")
            self.clear_all()
        
        with self.driver.session() as session:
            # 노드 생성
            print("\n  Creating nodes...")
            node_id_map = {}  # 기존 ID -> 새 ID 매핑
            
            for i, node in enumerate(nodes):
                old_id = node["id"]
                labels = ":".join(node["labels"])
                properties = node["properties"]
                
                # 노드 생성
                query = f"CREATE (n:{labels}) SET n = $properties RETURN elementId(n) as new_id"
                result = session.run(query, properties=properties)
                new_id = result.single()["new_id"]
                node_id_map[old_id] = new_id
                
                if (i + 1) % 100 == 0:
                    print(f"    Progress: {i + 1}/{len(nodes)}")
            
            print(f"  ✓ {len(nodes)} nodes created")
            
            # 관계 생성
            print("\n  Creating relationships...")
            for i, rel in enumerate(relationships):
                source_id = node_id_map.get(rel["source"])
                target_id = node_id_map.get(rel["target"])
                
                if source_id is None or target_id is None:
                    continue
                
                rel_type = rel["type"]
                properties = rel["properties"]
                
                query = f"""
                MATCH (a), (b)
                WHERE elementId(a) = $source_id AND elementId(b) = $target_id
                CREATE (a)-[r:{rel_type}]->(b)
                SET r = $properties
                """
                session.run(query, source_id=source_id, target_id=target_id, properties=properties)
                
                if (i + 1) % 100 == 0:
                    print(f"    Progress: {i + 1}/{len(relationships)}")
            
            print(f"  ✓ {len(relationships)} relationships created")
        
        print(f"\n✓ Import completed")
    
    def clear_all(self):
        """모든 데이터 삭제"""
        print("\n⚠️  WARNING: This will delete ALL data in the database!")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm != "DELETE":
            print("Cancelled.")
            return
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("✓ All data deleted")
    
    def list_backups(self):
        """백업 파일 목록 표시"""
        backups = sorted(BACKUP_DIR.glob("neo4j_backup_*.json"), reverse=True)
        
        if not backups:
            print("\nNo backups found.")
            return
        
        print("\n" + "="*70)
        print("Available Backups")
        print("="*70)
        
        for i, backup in enumerate(backups, 1):
            size = backup.stat().st_size / 1024 / 1024  # MB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i}. {backup.name}")
            print(f"   Size: {size:.2f} MB")
            print(f"   Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Neo4j Database Management Tool")
        print("\nUsage: python manage_neo4j.py <command> [options]")
        print("\nCommands:")
        print("  stats              - Show database statistics")
        print("  export [file]      - Export database to JSON")
        print("  import <file>      - Import database from JSON")
        print("  clear              - Clear all data (with confirmation)")
        print("  backups            - List available backups")
        print("\nExamples:")
        print("  python manage_neo4j.py stats")
        print("  python manage_neo4j.py export")
        print("  python manage_neo4j.py export my_backup.json")
        print("  python manage_neo4j.py import backups/neo4j_backup_20260119_120000.json")
        print("  python manage_neo4j.py backups")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Neo4j 연결
    manager = Neo4jManager()
    if not manager.connect():
        sys.exit(1)
    
    try:
        if command == "stats":
            manager.print_stats()
        
        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            manager.export_to_json(output_file)
        
        elif command == "import":
            if len(sys.argv) < 3:
                print("Error: Please specify input file")
                sys.exit(1)
            input_file = sys.argv[2]
            manager.import_from_json(input_file, clear_before=False)
        
        elif command == "clear":
            manager.clear_all()
        
        elif command == "backups":
            manager.list_backups()
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    finally:
        manager.close()


if __name__ == "__main__":
    main()
