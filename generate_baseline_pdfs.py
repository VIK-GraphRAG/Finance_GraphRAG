"""
Generate baseline PDF documents for Tech-Analyst GraphRAG
Creates sample PDFs for supply chain, risks, regulations, and tech roadmap
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime


def create_supply_chain_pdf():
    """Create supply chain mapping PDF"""
    filename = "data/baseline/supply_chain_mapping.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Semiconductor Supply Chain Mapping", title_style))
    story.append(Paragraph("ASML → TSMC → Nvidia → CSP Analysis", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    # Content
    content = [
        ("Executive Summary", """
        The global semiconductor supply chain is highly concentrated and interdependent. 
        ASML holds a monopoly on EUV lithography systems, which are essential for manufacturing 
        advanced chips below 7nm. TSMC dominates the foundry market with 60% market share, 
        manufacturing chips for Nvidia, AMD, and Apple. This concentration creates significant 
        supply chain risks.
        """),
        
        ("Critical Dependencies", """
        <b>1. ASML → TSMC Dependency:</b><br/>
        TSMC's 3nm and below processes are 100% dependent on ASML's EUV systems. 
        Each EUV machine costs $150-200M and has 18-month lead times. ASML can produce 
        approximately 60 systems per year, creating a bottleneck for capacity expansion.
        <br/><br/>
        <b>2. TSMC → Nvidia Dependency:</b><br/>
        Nvidia manufactures 100% of its H100/H200 GPUs at TSMC using CoWoS advanced packaging. 
        This dependency level is critical, as no alternative foundry can currently produce 
        equivalent performance chips. AMD faces similar dependency with its MI300 series.
        <br/><br/>
        <b>3. SK Hynix → Nvidia HBM Supply:</b><br/>
        SK Hynix supplies approximately 50% of Nvidia's HBM3E requirements. The company's 
        HBM production capacity is fully allocated through 2025, creating supply constraints 
        for AI accelerators.
        """),
        
        ("Geopolitical Concentration Risk", """
        <b>Taiwan Concentration:</b><br/>
        TSMC's primary manufacturing facilities are located in Taiwan, producing over 90% 
        of the world's most advanced chips. Taiwan Strait tensions create systemic risk 
        for the entire AI and semiconductor industry. Alternative fabs in Arizona and Japan 
        won't reach significant capacity until 2026-2027.
        <br/><br/>
        <b>Netherlands Export Controls:</b><br/>
        ASML, based in the Netherlands, is subject to export restrictions on EUV systems 
        to China. This creates geopolitical leverage points and potential supply disruptions 
        if relations deteriorate.
        """),
        
        ("Supply Chain Resilience Efforts", """
        <b>CHIPS Act (USA):</b><br/>
        $52B in subsidies to build domestic semiconductor manufacturing. TSMC is constructing 
        two fabs in Arizona (5nm and 3nm), Intel is expanding in Ohio and Arizona, and 
        Samsung is building a fab in Texas.
        <br/><br/>
        <b>Dual Sourcing Strategies:</b><br/>
        Nvidia is diversifying HBM suppliers by qualifying Samsung and Micron alongside 
        SK Hynix. However, process qualification takes 12-18 months, limiting short-term 
        flexibility.
        <br/><br/>
        <b>Alternative Architectures:</b><br/>
        Cloud providers (AWS, Google) are developing custom chips (Trainium, TPU) to reduce 
        dependency on Nvidia. However, software ecosystem lock-in (CUDA) maintains Nvidia's 
        competitive moat.
        """),
        
        ("Supply Chain Vulnerability Assessment", """
        <b>Critical Single Points of Failure:</b><br/>
        1. ASML EUV systems (no alternative supplier)<br/>
        2. TSMC advanced packaging (CoWoS, InFO)<br/>
        3. Taiwan-based manufacturing (geopolitical risk)<br/>
        4. HBM production capacity (12-month lead times)<br/>
        5. Rare earth materials (China controls 80% of supply)
        <br/><br/>
        <b>Risk Mitigation Timeline:</b><br/>
        - Short-term (2024-2025): Limited options, inventory buffer only<br/>
        - Medium-term (2026-2027): New fabs coming online (Arizona, Japan)<br/>
        - Long-term (2028+): Geographic diversification achievable
        """),
    ]
    
    for heading, text in content:
        story.append(Paragraph(heading, styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(text, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    print(f"✅ Created: {filename}")


def create_risk_factors_pdf():
    """Create industry risk factors PDF"""
    filename = "data/baseline/industry_risk_factors.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Technology Industry Risk Factors", title_style))
    story.append(Paragraph("Geopolitical, Power, and Interest Rate Analysis", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    content = [
        ("1. Geopolitical Risks", """
        <b>US-China Technology Decoupling:</b><br/>
        Export controls on advanced chips (below 7nm) and semiconductor equipment have 
        fragmented the global market. Chinese companies cannot access Nvidia H100/A100 GPUs, 
        creating a separate ecosystem. This affects $50B+ in annual semiconductor exports.
        <br/><br/>
        <b>Taiwan Strait Tensions:</b><br/>
        Severity: Critical (9/10)<br/>
        TSMC produces 92% of advanced chips globally. Military conflict or blockade scenarios 
        would halt production, causing immediate supply shortages for AI, automotive, and 
        consumer electronics. Economic impact estimated at $1T+ globally.
        <br/><br/>
        <b>EU Technology Sovereignty:</b><br/>
        EU is investing €43B in semiconductor manufacturing to reduce dependency on Asia. 
        However, timeline extends to 2030, providing limited near-term risk mitigation.
        """),
        
        ("2. Power Supply Constraints", """
        <b>Data Center Power Consumption:</b><br/>
        A single H100 GPU consumes 700W. A 100,000-GPU cluster requires 200+ MW of power, 
        equivalent to a small city. Major cloud providers are facing power allocation 
        constraints in key markets (Virginia, Singapore).
        <br/><br/>
        <b>Semiconductor Manufacturing Energy Intensity:</b><br/>
        A modern 3nm fab consumes 150-200 MW continuously. Taiwan already faces periodic 
        power shortages, risking production interruptions. TSMC's Arizona fabs will require 
        new power infrastructure.
        <br/><br/>
        <b>Renewable Energy Transition Pressure:</b><br/>
        Tech companies have committed to 100% renewable energy, but AI growth is outpacing 
        green power availability. This creates procurement competition and cost increases.
        """),
        
        ("3. Interest Rate Sensitivity", """
        <b>CAPEX Investment Impact:</b><br/>
        Semiconductor fabs require $20-30B investments with 5-7 year payback periods. 
        Higher interest rates (5% vs 0%) increase financing costs by $5-7B over project life. 
        This defers expansion plans and reduces industry capacity growth.
        <br/><br/>
        <b>Valuation Multiple Compression:</b><br/>
        Technology stocks trade at 25-40x P/E ratios, sensitive to discount rate changes. 
        A 100bps rate increase can reduce valuations by 10-15%, affecting M&A activity 
        and strategic investments.
        <br/><br/>
        <b>Corporate Debt Refinancing:</b><br/>
        Intel and other capital-intensive companies face higher refinancing costs. 
        Intel's $50B debt at 5% rates adds $2.5B annual interest expense vs 2% historical rates.
        """),
        
        ("4. Talent and IP Risks", """
        <b>Semiconductor Expertise Shortage:</b><br/>
        Building new fabs requires thousands of specialized engineers. TSMC Arizona faces 
        challenges recruiting talent, delaying production ramp. Training timelines: 2-3 years.
        <br/><br/>
        <b>IP Theft and Cyber Espionage:</b><br/>
        Advanced chip designs represent billions in R&D. State-sponsored IP theft targets 
        EUV lithography, advanced packaging, and AI chip architectures. Estimated impact: 
        $200-300B in lost competitive advantage.
        """),
        
        ("5. Regulatory Compliance Risks", """
        <b>Environmental Regulations:</b><br/>
        Semiconductor manufacturing uses hazardous chemicals and significant water resources. 
        Stricter environmental standards in US/EU increase operating costs by 15-20% vs 
        Asian facilities.
        <br/><br/>
        <b>AI Governance and Export Controls:</b><br/>
        Evolving AI regulations (EU AI Act, potential US legislation) may restrict GPU 
        sales for certain applications. High-risk AI systems face compliance burdens, 
        potentially reducing addressable market.
        """),
    ]
    
    for heading, text in content:
        story.append(Paragraph(heading, styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(text, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    print(f"✅ Created: {filename}")


def create_regulation_pdf():
    """Create regulation guidelines PDF"""
    filename = "data/baseline/regulation_guidelines.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Regulation Guidelines & Policy Analysis", title_style))
    story.append(Paragraph("CHIPS Act, EU AI Act, Export Controls", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    content = [
        ("CHIPS and Science Act (USA)", """
        <b>Overview:</b><br/>
        Enacted August 2022. $52.7B in subsidies for semiconductor manufacturing and R&D 
        in the United States. Goal: reduce dependency on Asian semiconductor production 
        and strengthen domestic supply chain resilience.
        <br/><br/>
        <b>Funding Allocation:</b><br/>
        - $39B for manufacturing incentives<br/>
        - $13.2B for R&D and workforce development<br/>
        - $500M for international cooperation<br/>
        - Investment tax credit: 25% for fab construction
        <br/><br/>
        <b>Major Recipients:</b><br/>
        - Intel: $8.5B for Arizona, Ohio, New Mexico fabs<br/>
        - TSMC: $6.6B for Arizona fabs (4nm, 3nm, 2nm)<br/>
        - Samsung: $6.4B for Texas fab expansion<br/>
        - Micron: $6.1B for New York memory fab<br/>
        - GlobalFoundries: $1.5B for Malta, NY expansion
        <br/><br/>
        <b>Guardrails and Restrictions:</b><br/>
        Recipients cannot expand advanced semiconductor manufacturing capacity in China 
        for 10 years. This particularly impacts Intel and Samsung, which have existing 
        China operations. Violation results in full subsidy repayment.
        <br/><br/>
        <b>Impact Assessment:</b><br/>
        Expected to add 500K wafers per month of domestic capacity by 2030. However, 
        this represents only 15% of global advanced node production. Taiwan concentration 
        risk remains significant through 2028.
        """),
        
        ("EU AI Act", """
        <b>Overview:</b><br/>
        World's first comprehensive AI regulation, approved March 2024. Establishes 
        risk-based framework for AI systems, with implications for semiconductor companies 
        supplying AI infrastructure.
        <br/><br/>
        <b>Risk Categories:</b><br/>
        - Unacceptable Risk: Banned (social scoring, real-time biometric surveillance)<br/>
        - High Risk: Strict requirements (healthcare, critical infrastructure, law enforcement)<br/>
        - Limited Risk: Transparency obligations (chatbots, deepfakes)<br/>
        - Minimal Risk: No restrictions (spam filters, video games)
        <br/><br/>
        <b>Foundation Model Requirements:</b><br/>
        Models with >10^25 FLOPs (e.g., GPT-4, Claude) must:<br/>
        - Conduct systemic risk assessments<br/>
        - Implement cybersecurity measures<br/>
        - Report serious incidents<br/>
        - Ensure energy efficiency<br/>
        This affects demand for large-scale GPU clusters in EU.
        <br/><br/>
        <b>Semiconductor Industry Impact:</b><br/>
        GPU sales for high-risk AI applications require customer compliance verification. 
        Nvidia, AMD, and Intel must implement tracking systems for EU sales. Estimated 
        compliance cost: $200-300M annually for major chip makers.
        <br/><br/>
        <b>Enforcement Timeline:</b><br/>
        - Prohibited AI: Ban effective February 2025<br/>
        - Foundation models: Compliance by August 2025<br/>
        - High-risk AI: Full compliance by August 2026<br/>
        Penalties: Up to €35M or 7% of global revenue
        """),
        
        ("US Export Controls on Advanced Chips", """
        <b>October 2022 and October 2023 Rules:</b><br/>
        Restrict export of advanced chips and semiconductor manufacturing equipment to China. 
        Specifically targets AI and supercomputing applications.
        <br/><br/>
        <b>Restricted Products:</b><br/>
        - GPUs: Nvidia A100/H100/H200, AMD MI250/MI300<br/>
        - Chip-making equipment: EUV lithography, advanced deposition tools<br/>
        - Design software: EDA tools for sub-16nm processes<br/>
        - Parameters: >300 TOPS for AI, >600GB/s interconnect bandwidth
        <br/><br/>
        <b>China-specific Products:</b><br/>
        Nvidia created "China versions" with reduced specs:<br/>
        - A800 (vs A100): 400GB/s interconnect vs 600GB/s<br/>
        - H800 (vs H100): 300GB/s interconnect vs 900GB/s<br/>
        October 2023 rules closed these loopholes.
        <br/><br/>
        <b>Financial Impact:</b><br/>
        - Nvidia: $5B annual revenue loss (10% of data center segment)<br/>
        - AMD: $1B annual revenue impact<br/>
        - ASML: Cannot sell EUV systems to China (estimated $3-4B opportunity cost)<br/>
        - Applied Materials: Restricted from selling advanced tools ($2B revenue impact)
        <br/><br/>
        <b>Strategic Implications:</b><br/>
        Accelerates China's domestic semiconductor development efforts. Increased funding 
        for SMIC, Huawei, and local equipment makers. Long-term risk of parallel technology 
        ecosystems and reduced US market share.
        """),
        
        ("China Semiconductor Policy", """
        <b>Response to US Export Controls:</b><br/>
        "Big Fund Phase III": $47B fund for domestic semiconductor development. Focus on 
        equipment self-sufficiency and mature node (28nm+) capacity expansion.
        <br/><br/>
        <b>Rare Earth Export Restrictions:</b><br/>
        China controls 80% of rare earth processing. December 2023 export controls on 
        gallium and germanium affect semiconductor and solar panel manufacturing globally.
        <br/><br/>
        <b>Cybersecurity and Data Laws:</b><br/>
        All companies operating in China must store data locally and pass security reviews. 
        This affects cloud providers using US chips and creates compliance complexity.
        """),
    ]
    
    for heading, text in content:
        story.append(Paragraph(heading, styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(text, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    print(f"✅ Created: {filename}")


def create_tech_roadmap_pdf():
    """Create technology roadmap PDF"""
    filename = "data/baseline/tech_roadmap.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Semiconductor Technology Roadmap", title_style))
    story.append(Paragraph("2nm, HBM4, Advanced Packaging Milestones", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))
    
    content = [
        ("Process Technology Evolution", """
        <b>TSMC Roadmap:</b><br/>
        - 3nm (N3): Mass production Q4 2022, Apple A17 Pro first customer<br/>
        - 3nm Enhanced (N3E): Q4 2023, improved yield and cost<br/>
        - 2nm (N2): Volume production H2 2025, GAA transistors<br/>
        - 2nm Plus (N2P): 2026, 10-15% performance improvement<br/>
        - 1.4nm (A14): 2027 target, next-generation GAA
        <br/><br/>
        <b>Samsung Foundry Roadmap:</b><br/>
        - 3nm GAA (3GAP): Q4 2022 launch, yield challenges<br/>
        - 2nm (2GAP): 2025 target, competing with TSMC N2<br/>
        - 1.4nm: 2027 target<br/>
        Note: Samsung has faced persistent yield issues with GAA transition, losing market 
        share to TSMC.
        <br/><br/>
        <b>Intel Process Roadmap:</b><br/>
        - Intel 4 (7nm): Meteor Lake launched Q4 2023<br/>
        - Intel 3 (enhanced 7nm): 2024, 18% performance gain<br/>
        - Intel 20A (2nm equivalent): H1 2024, first Intel GAA<br/>
        - Intel 18A (1.8nm): 2025, targeting external customers<br/>
        - Intel 14A: 2026-2027
        <br/><br/>
        <b>Critical Technology Transitions:</b><br/>
        GAA (Gate-All-Around) transistors replace FinFET at 2nm node. This enables continued 
        transistor density scaling but requires entirely new manufacturing processes. 
        Development cost: $30B+ per company.
        """),
        
        ("HBM (High Bandwidth Memory) Evolution", """
        <b>HBM3 (Current Generation):</b><br/>
        - Bandwidth: 819GB/s per stack<br/>
        - Capacity: up to 24GB per stack<br/>
        - Power efficiency: 3.2 pJ/bit<br/>
        - Production: SK Hynix (50% share), Samsung (30%), Micron (20%)
        <br/><br/>
        <b>HBM3E (Enhanced, 2024):</b><br/>
        - Bandwidth: 1.15TB/s per stack (40% increase)<br/>
        - Capacity: up to 36GB per stack<br/>
        - Power efficiency: 2.8 pJ/bit<br/>
        - Mass production: SK Hynix Q3 2024, Samsung Q4 2024<br/>
        - Primary customer: Nvidia H200, AMD MI325X
        <br/><br/>
        <b>HBM4 (2026 Target):</b><br/>
        - Bandwidth target: 2TB/s per stack<br/>
        - Capacity: up to 48GB per stack<br/>
        - New features: Error correction, higher stack height (16-hi)<br/>
        - Technology: Through-Silicon Via (TSV) improvements<br/>
        - Development status: SK Hynix and Nvidia co-developing
        <br/><br/>
        <b>Supply Chain Bottleneck:</b><br/>
        HBM production requires specialized equipment and has 12-month qualification cycles. 
        Current shortage limits AI accelerator production. SK Hynix HBM capacity fully 
        allocated through 2025. New fabs coming online in 2026 will ease constraints.
        """),
        
        ("Advanced Packaging Technologies", """
        <b>CoWoS (Chip-on-Wafer-on-Substrate) - TSMC:</b><br/>
        - Current: CoWoS-S (interposer-based), used in Nvidia H100<br/>
        - 2024: CoWoS-L (LSI interposer), 3x size increase<br/>
        - 2025: CoWoS-R (RDL-based), cost reduction<br/>
        - Capacity: 15K wafers/month (2024) → 30K wafers/month (2025)<br/>
        Bottleneck: CoWoS capacity limits H100/H200 production
        <br/><br/>
        <b>InFO (Integrated Fan-Out) - TSMC:</b><br/>
        - Used for mobile processors (Apple A-series)<br/>
        - Lower cost than CoWoS, less suited for HBM integration<br/>
        - 2025: InFO_oS (on Substrate) for improved power delivery
        <br/><br/>
        <b>Foveros - Intel:</b><br/>
        - 3D stacking of active logic dies<br/>
        - Used in Meteor Lake (compute + graphics stacking)<br/>
        - 2025: Foveros Direct (10μm bump pitch)<br/>
        - Target: compete with TSMC for external customers
        <br/><br/>
        <b>X-Cube - Samsung:</b><br/>
        - Hybrid bonding technology for 3D integration<br/>
        - Currently in development, lagging TSMC/Intel<br/>
        - Target production: 2025-2026
        """),
        
        ("EUV Lithography Evolution", """
        <b>Current EUV (0.33 NA):</b><br/>
        - Minimum pitch: 13nm<br/>
        - Used for: 7nm through 2nm processes<br/>
        - ASML production: 60 systems/year capacity
        <br/><br/>
        <b>High-NA EUV (0.55 NA):</b><br/>
        - Minimum pitch: 8nm (enables sub-2nm processes)<br/>
        - First system delivered to Intel in December 2023<br/>
        - Cost: $380M per system (vs $200M for standard EUV)<br/>
        - ASML production: 10-20 systems/year initially<br/>
        - Customer roadmap: Intel (2024), TSMC (2025), Samsung (2026)
        <br/><br/>
        <b>Technology Challenges:</b><br/>
        High-NA systems require complete process redesign. Wafer size changes from 300mm 
        to effectively 200mm throughput, increasing costs. Multi-year learning curve expected.
        """),
        
        ("AI Accelerator Roadmap", """
        <b>Nvidia GPU Evolution:</b><br/>
        - 2023: H100 (Hopper architecture, 4nm)<br/>
        - 2024: H200 (HBM3E upgrade, 141GB vs 80GB)<br/>
        - 2024: B100/B200 (Blackwell architecture, 4nm)<br/>
        - 2025: B200 Ultra (3nm process shrink)<br/>
        - 2026: Next-gen (codename Rubin, 3nm+ or 2nm)
        <br/><br/>
        <b>AMD GPU Competition:</b><br/>
        - 2023: MI300A/MI300X (chiplet architecture, 5nm+6nm)<br/>
        - 2024: MI325X (HBM3E, 256GB)<br/>
        - 2025: MI350 (3nm target, competing with B100)<br/>
        Software ecosystem gap remains AMD's challenge vs CUDA.
        <br/><br/>
        <b>Custom Silicon Trend:</b><br/>
        - AWS Trainium2 (2024): competing with Nvidia for training workloads<br/>
        - Google TPU v5 (2024): 4x performance vs v4<br/>
        - Microsoft Maia (2024): Azure OpenAI infrastructure<br/>
        - Meta MTIA v2 (2025): inference optimization<br/>
        Custom chips now represent 20% of AI accelerator market, growing to 35% by 2027.
        """),
    ]
    
    for heading, text in content:
        story.append(Paragraph(heading, styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(text, styles['BodyText']))
        story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    print(f"✅ Created: {filename}")


if __name__ == "__main__":
    print("📄 Generating baseline PDF documents...")
    print("="*60)
    
    create_supply_chain_pdf()
    create_risk_factors_pdf()
    create_regulation_pdf()
    create_tech_roadmap_pdf()
    
    print("="*60)
    print("✅ All baseline PDFs generated successfully!")
    print("\nFiles created in data/baseline/:")
    print("  - supply_chain_mapping.pdf")
    print("  - industry_risk_factors.pdf")
    print("  - regulation_guidelines.pdf")
    print("  - tech_roadmap.pdf")
