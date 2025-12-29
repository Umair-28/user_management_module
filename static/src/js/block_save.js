/** @odoo-module **/

document.addEventListener('click', async (ev) => {

    if(!window.location.href.includes('/odoo/org-chart/new') && !window.location.href.includes('/odoo/employees/new')) return
    // 1. Target the Save buttons only
    const saveBtn = ev.target.closest('.o_form_button_save, .o_form_button_save_new');
    if (!saveBtn) return;

    console.log("DOM Hack: Save clicked. Checking user_id_1...");

    // 2. Try to find the input by ID
    let userInput = document.getElementById('user_id_1');

    // 3. If it's not found, it's hidden in the Settings Tab
    if (!userInput) {
        console.log("DOM Hack: ID 'user_id_1' not found. Clicking Settings Tab...");
        
        // Find and click the Settings tab
        const settingsTab = Array.from(document.querySelectorAll('.nav-link'))
                                 .find(el => el.textContent.trim() === 'Settings');
        
        if (settingsTab) {
            settingsTab.click();
            
            // Wait 200ms for Odoo to render the HTML for that tab
            await new Promise(r => setTimeout(r, 200));
            
            // Re-try finding the ID
            userInput = document.getElementById('user_id_1');
        }
    }

    // 4. Final Validation
    if (userInput) {
        const val = userInput.value.trim();
        console.log("DOM Hack: Value of user_id_1 is: '" + val + "'");

        if (val === "") {
            console.error("DOM Hack: BLOCKING SAVE. Field is empty.");
            
            // Stop Odoo from saving
            ev.stopPropagation();
            ev.preventDefault();
            
            // Visual warning
            userInput.style.setProperty("border", "2px solid red", "important");
            userInput.focus();
            
            alert("STOP! The Related User field cannot be empty.");
        }
    } else {
        console.error("DOM Hack: Even after tab switch, ID 'user_id_1' was not found in the DOM.");
    }
}, true); // 'true' ensures we catch the click before Odoo does