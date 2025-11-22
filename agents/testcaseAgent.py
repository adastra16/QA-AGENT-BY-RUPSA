# agents/testcaseAgent.py

def generate_test_cases(context_text: str) -> str:
    """
    Local dummy generator for test cases.
    No OpenAI, no API key required.
    """

    return f"""
### Generated Test Cases (Local)

1. **Test Case: Verify Checkout Flow**
   - **Precondition:** User is logged in and has items in cart.
   - **Steps:**
       1. Go to checkout page.
       2. Verify shipping details.
       3. Apply discount if available.
       4. Click 'Place Order'.
   - **Expected Result:** Order should be placed successfully.

2. **Test Case: Discount Application**
   - **Precondition:** Discount code exists.
   - **Steps:**
       1. Enter discount code.
       2. Click 'Apply'.
   - **Expected Result:** Discount should be applied to order summary.

3. **Test Case: Invalid Discount Code**
   - **Steps:**
       1. Enter invalid code.
       2. Click 'Apply'.
   - **Expected Result:** User sees error message.

(Generated without OpenAI — local rules-based output)
"""
