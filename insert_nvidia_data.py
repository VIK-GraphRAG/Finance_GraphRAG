"""
Insert sample NVIDIA data for testing
"""
import requests
import json

# Sample NVIDIA financial report
nvidia_data = """
NVIDIA Corporation Q4 FY2024 Financial Results

Company Overview:
NVIDIA Corporation is a leading technology company specializing in graphics processing units (GPUs) and artificial intelligence (AI) chips.

Key Executives:
- Jensen Huang, CEO and Founder
- Colette Kress, Executive VP and CFO
- Debora Shoquist, Executive VP of Operations

Financial Performance Q4 FY2024:
- Total Revenue: $22.1 billion (up 265% year-over-year)
- Data Center Revenue: $18.4 billion (up 409% year-over-year)
- Gaming Revenue: $2.9 billion (up 56% year-over-year)
- Professional Visualization Revenue: $463 million (up 105% year-over-year)
- Automotive Revenue: $281 million (up 8% year-over-year)

Full Year FY2024:
- Total Revenue: $60.9 billion (up 126% year-over-year)
- Net Income: $29.8 billion
- Gross Margin: 72.7%
- Operating Margin: 54.0%

Products and Technology:
- H100 Tensor Core GPU: Leading AI training and inference chip
- A100 GPU: Previous generation data center GPU
- GeForce RTX 4090: Consumer gaming GPU
- CUDA Platform: Software platform for GPU computing
- AI Enterprise Software: Enterprise AI software suite

Market Position:
NVIDIA dominates the AI chip market with approximately 80-95% market share in AI training chips.
Major competitors include AMD, Intel, and emerging startups like Cerebras.

Key Customers:
- Microsoft: Major customer for Azure cloud AI services
- Meta: AI training infrastructure
- Amazon Web Services: Cloud GPU instances
- Google Cloud: AI and ML services
- Tesla: Automotive AI chips

Supply Chain:
- TSMC (Taiwan Semiconductor Manufacturing Company): Primary chip manufacturer
- Samsung: Secondary chip supplier
- SK Hynix: Memory supplier (HBM - High Bandwidth Memory)

Strategic Partnerships:
NVIDIA partners with Oracle for cloud AI infrastructure.
NVIDIA collaborates with ServiceNow for enterprise AI applications.
NVIDIA works with SAP for business intelligence AI.

Geographic Revenue:
- United States: 45% of revenue
- China: 14% of revenue (affected by export restrictions)
- Taiwan: 12% of revenue
- Other: 29% of revenue

Growth Drivers:
- Generative AI boom and Large Language Model training demand
- Cloud service provider infrastructure expansion
- Automotive autonomous driving systems
- Healthcare AI applications
- Financial services AI adoption

Risks:
- Export restrictions to China affecting revenue
- Increased competition from AMD and Intel
- Potential supply chain disruptions from TSMC
- High customer concentration (top customers represent significant revenue)
- Rapid technological obsolescence requiring continuous innovation

Recent Announcements:
Jensen Huang announced new Blackwell GPU architecture in March 2024.
NVIDIA introduced Grace Hopper Superchip combining CPU and GPU.
Company announced $50 billion stock buyback program.

Employee Information:
NVIDIA employs approximately 29,600 people globally as of January 2024.
Company headquarters located in Santa Clara, California.
"""

# Insert data
print("📤 Inserting NVIDIA data into GraphRAG...")
try:
    response = requests.post(
        "http://localhost:8000/insert",
        json={"text": nvidia_data},
        timeout=300
    )
    
    if response.status_code == 200:
        print("✅ Successfully inserted NVIDIA data!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🔍 Testing query...")
try:
    response = requests.post(
        "http://localhost:8000/query",
        json={"question": "What is NVIDIA's revenue?", "mode": "local"},
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Query successful!")
        print(f"Answer: {result.get('answer', 'No answer')}")
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"❌ Query error: {e}")
