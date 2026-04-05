#!/usr/bin/env python3
"""
Chaos Engineering Demo Script
Demonstrates AI SRE Agent performing automated RCA against simulated failures
"""

import asyncio
import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx


class ChaosDemo:
    """Chaos Engineering Demo Runner"""
    
    def __init__(self, agent_url: str = "http://localhost:8080"):
        self.agent_url = agent_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.demo_results: List[Dict[str, Any]] = []
    
    async def run_full_demo(self) -> Dict[str, Any]:
        """Run the complete chaos engineering demo"""
        print("=" * 80)
        print("AI SRE Agent - Chaos Engineering Demo")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        demo_result = {
            "demo_id": f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "scenarios": [],
            "summary": {}
        }
        
        # Scenario 1: Pod Kill
        print("\n" + "=" * 80)
        print("SCENARIO 1: Pod Kill Simulation")
        print("=" * 80)
        scenario1 = await self.run_pod_kill_scenario()
        demo_result["scenarios"].append(scenario1)
        
        # Scenario 2: High Latency Injection
        print("\n" + "=" * 80)
        print("SCENARIO 2: High Latency Injection")
        print("=" * 80)
        scenario2 = await self.run_latency_scenario()
        demo_result["scenarios"].append(scenario2)
        
        # Scenario 3: CPU Stress
        print("\n" + "=" * 80)
        print("SCENARIO 3: CPU Stress Simulation")
        print("=" * 80)
        scenario3 = await self.run_cpu_stress_scenario()
        demo_result["scenarios"].append(scenario3)
        
        # Generate summary
        demo_result["end_time"] = datetime.now().isoformat()
        demo_result["summary"] = self._generate_summary(demo_result["scenarios"])
        
        # Print final report
        self._print_final_report(demo_result)
        
        return demo_result
    
    async def run_pod_kill_scenario(self) -> Dict[str, Any]:
        """Run pod kill scenario"""
        scenario = {
            "name": "Pod Kill",
            "type": "kill_pod",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        print("\n📋 Step 1: Injecting pod kill failure...")
        
        # Inject failure
        try:
            response = await self.client.post(
                f"{self.agent_url}/api/v1/chaos/inject",
                json={
                    "failure_type": "kill_pod",
                    "target_deployment": "demo-app",
                    "namespace": "default",
                    "duration_seconds": 60
                }
            )
            
            if response.status_code == 200:
                chaos_result = response.json()
                print(f"   ✅ Chaos injected: {chaos_result.get('experiment_id', 'unknown')}")
                scenario["steps"].append({
                    "step": "inject_chaos",
                    "status": "success",
                    "details": chaos_result
                })
            else:
                print(f"   ❌ Failed to inject chaos: {response.text}")
                scenario["steps"].append({
                    "step": "inject_chaos",
                    "status": "failed",
                    "error": response.text
                })
                return scenario
        except Exception as e:
            print(f"   ❌ Error injecting chaos: {e}")
            scenario["steps"].append({
                "step": "inject_chaos",
                "status": "error",
                "error": str(e)
            })
            return scenario
        
        # Wait for incident to propagate
        print("\n📋 Step 2: Waiting for incident to propagate (30s)...")
        await asyncio.sleep(30)
        scenario["steps"].append({
            "step": "wait",
            "status": "completed",
            "duration_seconds": 30
        })
        
        # Perform RCA
        print("\n📋 Step 3: Performing Root Cause Analysis...")
        try:
            response = await self.client.post(
                f"{self.agent_url}/api/v1/rca/analyze",
                json={
                    "incident_type": "pod_crash",
                    "service_name": "demo-app",
                    "namespace": "default",
                    "severity": "high"
                }
            )
            
            if response.status_code == 200:
                rca_report = response.json()
                print(f"   ✅ RCA Report Generated: {rca_report.get('incident_id', 'unknown')}")
                print(f"\n   🔍 Root Cause: {rca_report.get('root_cause', 'N/A')}")
                print(f"\n   📊 Severity: {rca_report.get('severity', 'N/A')}")
                print(f"\n   💡 Recommendations:")
                for i, rec in enumerate(rca_report.get('recommendations', []), 1):
                    print(f"      {i}. {rec}")
                
                scenario["steps"].append({
                    "step": "rca_analysis",
                    "status": "success",
                    "rca_report": rca_report
                })
                scenario["rca_report"] = rca_report
            else:
                print(f"   ❌ RCA analysis failed: {response.text}")
                scenario["steps"].append({
                    "step": "rca_analysis",
                    "status": "failed",
                    "error": response.text
                })
        except Exception as e:
            print(f"   ❌ Error during RCA: {e}")
            scenario["steps"].append({
                "step": "rca_analysis",
                "status": "error",
                "error": str(e)
            })
        
        scenario["end_time"] = datetime.now().isoformat()
        return scenario
    
    async def run_latency_scenario(self) -> Dict[str, Any]:
        """Run latency injection scenario"""
        scenario = {
            "name": "High Latency",
            "type": "inject_latency",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        print("\n📋 Step 1: Injecting network latency (500ms)...")
        
        try:
            response = await self.client.post(
                f"{self.agent_url}/api/v1/chaos/inject",
                json={
                    "failure_type": "inject_latency",
                    "target_deployment": "demo-app",
                    "namespace": "default",
                    "duration_seconds": 120,
                    "intensity": 0.5
                }
            )
            
            if response.status_code == 200:
                chaos_result = response.json()
                print(f"   ✅ Latency injected: {chaos_result.get('experiment_id', 'unknown')}")
                scenario["steps"].append({
                    "step": "inject_latency",
                    "status": "success",
                    "details": chaos_result
                })
            else:
                print(f"   ❌ Failed to inject latency: {response.text}")
                scenario["steps"].append({
                    "step": "inject_latency",
                    "status": "failed",
                    "error": response.text
                })
                return scenario
        except Exception as e:
            print(f"   ❌ Error injecting latency: {e}")
            scenario["steps"].append({
                "step": "inject_latency",
                "status": "error",
                "error": str(e)
            })
            return scenario
        
        print("\n📋 Step 2: Waiting for latency impact (30s)...")
        await asyncio.sleep(30)
        
        print("\n📋 Step 3: Performing Root Cause Analysis...")
        try:
            response = await self.client.post(
                f"{self.agent_url}/api/v1/rca/analyze",
                json={
                    "incident_type": "high_latency",
                    "service_name": "demo-app",
                    "namespace": "default",
                    "severity": "medium"
                }
            )
            
            if response.status_code == 200:
                rca_report = response.json()
                print(f"   ✅ RCA Report Generated: {rca_report.get('incident_id', 'unknown')}")
                print(f"\n   🔍 Root Cause: {rca_report.get('root_cause', 'N/A')}")
                print(f"\n   💡 Recommendations:")
                for i, rec in enumerate(rca_report.get('recommendations', []), 1):
                    print(f"      {i}. {rec}")
                
                scenario["steps"].append({
                    "step": "rca_analysis",
                    "status": "success",
                    "rca_report": rca_report
                })
                scenario["rca_report"] = rca_report
            else:
                print(f"   ❌ RCA analysis failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Error during RCA: {e}")
        
        scenario["end_time"] = datetime.now().isoformat()
        return scenario
    
    async def run_cpu_stress_scenario(self) -> Dict[str, Any]:
        """Run CPU stress scenario"""
        scenario = {
            "name": "CPU Stress",
            "type": "cpu_stress",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        print("\n📋 Step 1: Injecting CPU stress (80%)...")
        
        try:
            response = await self.client.post(
                f"{self.agent_url}/api/v1/chaos/inject",
                json={
                    "failure_type": "cpu_stress",
                    "target_deployment": "demo-app",
                    "namespace": "default",
                    "duration_seconds": 120,
                    "intensity": 0.8
                }
            )
            
            if response.status_code == 200:
                chaos_result = response.json()
                print(f"   ✅ CPU stress injected: {chaos_result.get('experiment_id', 'unknown')}")
                scenario["steps"].append({
                    "step": "inject_cpu_stress",
                    "status": "success",
                    "details": chaos_result
                })
            else:
                print(f"   ❌ Failed to inject CPU stress: {response.text}")
                return scenario
        except Exception as e:
            print(f"   ❌ Error injecting CPU stress: {e}")
            return scenario
        
        print("\n📋 Step 2: Waiting for CPU throttling impact (30s)...")
        await asyncio.sleep(30)
        
        print("\n📋 Step 3: Performing Root Cause Analysis...")
        try:
            response = await self.client.post(
                f"{self.agent_url}/api/v1/rca/analyze",
                json={
                    "incident_type": "cpu_throttling",
                    "service_name": "demo-app",
                    "namespace": "default",
                    "severity": "high"
                }
            )
            
            if response.status_code == 200:
                rca_report = response.json()
                print(f"   ✅ RCA Report Generated: {rca_report.get('incident_id', 'unknown')}")
                print(f"\n   🔍 Root Cause: {rca_report.get('root_cause', 'N/A')}")
                print(f"\n   💡 Recommendations:")
                for i, rec in enumerate(rca_report.get('recommendations', []), 1):
                    print(f"      {i}. {rec}")
                
                scenario["steps"].append({
                    "step": "rca_analysis",
                    "status": "success",
                    "rca_report": rca_report
                })
                scenario["rca_report"] = rca_report
            else:
                print(f"   ❌ RCA analysis failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Error during RCA: {e}")
        
        scenario["end_time"] = datetime.now().isoformat()
        return scenario
    
    def _generate_summary(self, scenarios: List[Dict]) -> Dict[str, Any]:
        """Generate demo summary"""
        total_scenarios = len(scenarios)
        successful_rcas = sum(1 for s in scenarios if s.get("rca_report"))
        
        return {
            "total_scenarios": total_scenarios,
            "successful_rcas": successful_rcas,
            "success_rate": f"{(successful_rcas / total_scenarios * 100):.1f}%" if total_scenarios > 0 else "0%",
            "recommendations_generated": sum(len(s.get("rca_report", {}).get("recommendations", [])) for s in scenarios)
        }
    
    def _print_final_report(self, demo_result: Dict[str, Any]):
        """Print final demo report"""
        print("\n" + "=" * 80)
        print("DEMO COMPLETE - FINAL REPORT")
        print("=" * 80)
        
        print(f"\nDemo ID: {demo_result['demo_id']}")
        print(f"Start Time: {demo_result['start_time']}")
        print(f"End Time: {demo_result['end_time']}")
        
        print("\n📊 Summary:")
        summary = demo_result["summary"]
        print(f"   Total Scenarios: {summary['total_scenarios']}")
        print(f"   Successful RCAs: {summary['successful_rcas']}")
        print(f"   Success Rate: {summary['success_rate']}")
        print(f"   Recommendations Generated: {summary['recommendations_generated']}")
        
        print("\n📁 Scenario Details:")
        for scenario in demo_result["scenarios"]:
            print(f"\n   {scenario['name']}:")
            if scenario.get("rca_report"):
                print(f"      Incident ID: {scenario['rca_report'].get('incident_id', 'N/A')}")
                print(f"      Severity: {scenario['rca_report'].get('severity', 'N/A')}")
                print(f"      Root Cause: {scenario['rca_report'].get('root_cause', 'N/A')[:100]}...")
            else:
                print("      Status: RCA not completed")
        
        print("\n" + "=" * 80)
    
    async def close(self):
        await self.client.aclose()


async def main():
    parser = argparse.ArgumentParser(description="AI SRE Agent Chaos Demo")
    parser.add_argument(
        "--agent-url",
        default="http://localhost:8080",
        help="URL of the AI SRE Agent API"
    )
    parser.add_argument(
        "--scenario",
        choices=["all", "pod-kill", "latency", "cpu-stress"],
        default="all",
        help="Which scenario to run"
    )
    parser.add_argument(
        "--output",
        default="demo_report.json",
        help="Output file for demo results"
    )
    
    args = parser.parse_args()
    
    demo = ChaosDemo(agent_url=args.agent_url)
    
    try:
        if args.scenario == "all":
            result = await demo.run_full_demo()
        elif args.scenario == "pod-kill":
            result = await demo.run_pod_kill_scenario()
        elif args.scenario == "latency":
            result = await demo.run_latency_scenario()
        elif args.scenario == "cpu-stress":
            result = await demo.run_cpu_stress_scenario()
        
        # Save results
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n📄 Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())
