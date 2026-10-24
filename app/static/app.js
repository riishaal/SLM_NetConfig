/**
 * SLM-Based Intelligent Network Configuration
 * Frontend Controller & API Integration
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('config-form');
  const requirementInput = document.getElementById('requirement-input');
  const deviceInput = document.getElementById('device-name');
  const generateBtn = document.getElementById('generate-btn');
  const btnSpinner = document.getElementById('btn-spinner');
  const btnText = document.getElementById('btn-text');

  const resultsArea = document.getElementById('results-area');
  const verificationStatus = document.getElementById('verification-status');
  const verificationSub = document.getElementById('verification-sub');
  const detectedCategory = document.getElementById('detected-category');
  const processingTime = document.getElementById('processing-time');
  const generatedConfigCode = document.getElementById('generated-config-code');
  const copyBtn = document.getElementById('copy-btn');
  const copyBtnText = document.getElementById('copy-btn-text');

  const infoRepoItem = document.getElementById('info-repo-item');
  const configLocationText = document.getElementById('config-location-text');
  const infoPtItem = document.getElementById('info-pt-item');
  const ptLocationText = document.getElementById('pt-location-text');

  const exampleBtns = document.querySelectorAll('.example-btn');

  // Example Requirements Data
  const examples = {
    1: 'Create VLAN 20 named Accounts.',
    2: 'Configure GigabitEthernet0/1 with IP address 192.168.20.1 and subnet mask 255.255.255.0.',
    3: 'Configure GigabitEthernet0/1 as a trunk port and allow VLANs 10 and 20.',
    4: 'Configure OSPF routing using network 192.168.1.0/24 in area 0.'
  };

  // Clickable example buttons: populate text box, user must still click Generate Configuration
  exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = btn.getAttribute('data-index');
      if (examples[idx]) {
        requirementInput.value = examples[idx];
        requirementInput.focus();

        // Highlight active example button
        exampleBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }
    });
  });

  // Handle Form Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const requirement = requirementInput.value.trim();
    const device = deviceInput.value.trim() || 'Switch1';

    if (!requirement) {
      requirementInput.focus();
      return;
    }

    // Set Loading State
    generateBtn.disabled = true;
    btnSpinner.style.display = 'inline-block';
    btnText.textContent = 'Generating Configuration...';

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          requirement: requirement,
          device: device
        })
      });

      const data = await response.json();

      if (!response.ok && !data.final_config) {
        throw new Error(data.error || 'Server error occurred while generating configuration.');
      }

      displayResults(data);

    } catch (err) {
      console.error('Generation Error:', err);
      displayError(err.message);
    } finally {
      // Restore Button State
      generateBtn.disabled = false;
      btnSpinner.style.display = 'none';
      btnText.textContent = 'Generate Configuration';
    }
  });

  // Display results from real backend
  function displayResults(data) {
    resultsArea.style.display = 'flex';

    // 1. Verification Result (APPROVED (PASSED), REFINEMENT NEEDED, or ERROR)
    const status = data.verification_status || (data.verified ? 'APPROVED (PASSED)' : 'REFINEMENT NEEDED');
    verificationStatus.textContent = status;
    verificationStatus.className = 'verification-badge';

    if (status.includes('APPROVED')) {
      verificationStatus.classList.add('approved');
      verificationSub.textContent = 'Syntax & semantic bounds passed closed-loop verification';
    } else if (status.includes('REFINEMENT')) {
      verificationStatus.classList.add('refinement');
      verificationSub.textContent = 'Refinement loop triggered to correct syntax/intent faults';
    } else {
      verificationStatus.classList.add('error');
      verificationSub.textContent = 'Configuration rejected or encountered syntax error';
    }

    // 2. Detected Category
    detectedCategory.textContent = data.detected_category || 'UNKNOWN';

    // 3. Processing Time
    const duration = typeof data.processing_time_sec === 'number' 
      ? data.processing_time_sec.toFixed(3) + 's' 
      : (data.processing_time_sec || 'N/A');
    processingTime.textContent = duration;

    // 4. Generated Cisco Configuration
    generatedConfigCode.textContent = data.final_config || '! No configuration generated or error occurred.';

    // 5. Processing Information (Paths)
    if (data.config_output_location) {
      configLocationText.textContent = data.config_output_location;
      infoRepoItem.style.display = 'flex';
    } else {
      infoRepoItem.style.display = 'none';
    }

    if (data.packet_tracer_export_location) {
      ptLocationText.textContent = data.packet_tracer_export_location;
      infoPtItem.style.display = 'flex';
    } else {
      infoPtItem.style.display = 'none';
    }

    // Smooth scroll to results
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Display error state if network or backend fails
  function displayError(errorMessage) {
    resultsArea.style.display = 'flex';
    verificationStatus.textContent = 'ERROR';
    verificationStatus.className = 'verification-badge error';
    verificationSub.textContent = errorMessage;

    detectedCategory.textContent = 'ERROR';
    processingTime.textContent = '0.000s';
    generatedConfigCode.textContent = `! Execution Error:\n! ${errorMessage}`;

    infoRepoItem.style.display = 'none';
    infoPtItem.style.display = 'none';

    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Copy Configuration Button Handler
  copyBtn.addEventListener('click', async () => {
    const textToCopy = generatedConfigCode.textContent;
    if (!textToCopy) return;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(textToCopy);
      } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }

      copyBtnText.textContent = 'Copied!';
      copyBtn.style.borderColor = '#10b981';
      copyBtn.style.color = '#059669';

      setTimeout(() => {
        copyBtnText.textContent = 'Copy Configuration';
        copyBtn.style.borderColor = '';
        copyBtn.style.color = '';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  });

});
