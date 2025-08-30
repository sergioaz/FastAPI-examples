from typing import List, Dict
from killswitch import killswitch_manager, OrderRequest
import asyncio
import time
from datetime import datetime

# Business Logic Classes
class EcommerceAPI:
    def __init__(self):
        self.killswitch = killswitch_manager

    async def create_order(self, order_data: OrderRequest) -> dict:
        """Create order with killswitch protection"""
        try:
            # KILLSWITCH: Orders (critical business function)
            if not self.killswitch.is_feature_enabled("order_creation"):
                return {
                    "error": "Order creation temporarily disabled",
                    "code": 503,
                    "retry_after": 300
                }

            # KILLSWITCH: Third-party integrations (can fail)
            inventory_check = True
            if self.killswitch.is_feature_enabled("inventory_service"):
                try:
                    inventory_check = await self.check_inventory(order_data.items)
                except Exception as e:
                    # Track error for auto-disable
                    await self.killswitch.auto_disable_on_errors("inventory_service", str(e))

                    # Proceed without check if killswitch allows
                    if not self.killswitch.is_feature_enabled("require_inventory_check"):
                        inventory_check = True  # Allow order anyway
                    else:
                        return {
                            "error": "Inventory check required but service unavailable",
                            "code": 503
                        }

            if not inventory_check:
                return {"error": "Insufficient inventory", "code": 400}

            # KILLSWITCH: Payment processing (critical)
            if not self.killswitch.is_feature_enabled("payment_processing"):
                # Maybe allow "pay later" orders
                order_result = await self.save_order({
                    **order_data.dict(),
                    "payment_status": "pending",
                    "notes": "Payment processing disabled - manual processing required"
                })
                return {
                    "order_id": order_result["id"],
                    "status": "pending_payment",
                    "message": "Order created - payment will be processed manually"
                }
            else:
                try:
                    payment_result = await self.process_payment(order_data)
                    if not payment_result["success"]:
                        return {
                            "error": "Payment failed",
                            "details": payment_result,
                            "code": 402
                        }
                except Exception as e:
                    # Track payment errors
                    await self.killswitch.auto_disable_on_errors("payment_processing", str(e))
                    raise

            # Save successful order
            order_result = await self.save_order({
                **order_data.dict(),
                "payment_status": "completed"
            })

            return {
                "order_id": order_result["id"],
                "status": "success",
                "total": order_data.total_amount
            }

        except Exception as e:
            await self.killswitch.auto_disable_on_errors("order_creation", str(e))
            return {"error": "Order creation failed", "details": str(e), "code": 500}

    async def check_inventory(self, items: List[Dict]) -> bool:
        """Mock inventory check"""
        # Simulate external service call
        await asyncio.sleep(0.1)

        # Simulate random failures for demonstration
        import random
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Inventory service timeout")

        return True

    async def process_payment(self, order_data: OrderRequest) -> dict:
        """Mock payment processing"""
        await asyncio.sleep(0.2)

        # Simulate payment failures
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Payment gateway error")

        if random.random() < 0.1:  # 10% decline rate
            return {"success": False, "error": "Card declined"}

        return {"success": True, "transaction_id": f"tx_{int(time.time())}"}

    async def save_order(self, order_data: dict) -> dict:
        """Mock order saving"""
        return {
            "id": f"order_{int(time.time())}_{order_data['user_id']}",
            "created_at": datetime.now().isoformat()
        }

