// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const researchTopicInput = document.getElementById('researchTopic');
    const startResearchBtn = document.getElementById('startResearchBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessageDiv = document.getElementById('errorMessage');
    
    const reportSectionDiv = document.getElementById('reportSection');
    const reportTopicH2 = document.getElementById('reportTopic');
    const reportContentDiv = document.getElementById('reportContent');
    const chartsContainerDiv = document.getElementById('chartsContainer');

    const followUpQuestionInput = document.getElementById('followUpQuestion');
    const askFollowUpBtn = document.getElementById('askFollowUpBtn');
    const followUpLoadingIndicator = document.getElementById('followUpLoadingIndicator');
    const followUpErrorMessageDiv = document.getElementById('followUpErrorMessage');
    const followUpAnswerDiv = document.getElementById('followUpAnswer');

    let currentReportData = null; // To store the full report response for follow-ups
    let chartInstances = []; // To keep track of Chart.js instances

    // Configure marked to handle line breaks like GitHub Flavored Markdown
    marked.setOptions({
        breaks: true, // GFM line breaks
        gfm: true,    // Use GFM
        sanitize: false // Be careful with this if content can be user-generated. For AI output, it's usually fine.
                       // Consider using DOMPurify if you need stronger sanitization.
    });

    function displayError(message, element = errorMessageDiv) {
        element.textContent = message;
        element.style.display = 'block';
    }

    function clearError(element = errorMessageDiv) {
        element.textContent = '';
        element.style.display = 'none';
    }

    function renderMarkdown(text, element) {
        if (text) {
            element.innerHTML = marked.parse(text);
        } else {
            element.innerHTML = '';
        }
    }

    startResearchBtn.addEventListener('click', async () => {
        const topic = researchTopicInput.value.trim();
        if (!topic) {
            displayError('Please enter a research topic.');
            return;
        }

        clearError();
        reportSectionDiv.style.display = 'none';
        reportContentDiv.innerHTML = '';
        chartsContainerDiv.innerHTML = '';
        chartInstances.forEach(chart => chart.destroy()); // Destroy old charts
        chartInstances = [];
        followUpAnswerDiv.innerHTML = '';
        followUpQuestionInput.value = '';


        loadingIndicator.style.display = 'block';
        startResearchBtn.disabled = true;

        try {
            const response = await fetch('/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: topic })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
            }

            currentReportData = await response.json();
            displayReport(currentReportData);

        } catch (error) {
            console.error('Research error:', error);
            displayError(`Failed to get research report: ${error.message}`);
        } finally {
            loadingIndicator.style.display = 'none';
            startResearchBtn.disabled = false;
        }
    });

    function displayReport(data) {
        reportTopicH2.textContent = `Report on: ${data.topic}`;
        reportContentDiv.innerHTML = ''; // Clear previous content

        const sections = [
            data.summary,
            data.medical_data_analysis,
            data.trends_analysis,
            data.government_schemes,
            data.diseases_on_rise
        ];

        sections.forEach(sectionData => {
            if (sectionData && sectionData.content) {
                const sectionEl = document.createElement('div');
                sectionEl.classList.add('report-subsection');
                
                const titleEl = document.createElement('h3');
                titleEl.textContent = sectionData.title;
                sectionEl.appendChild(titleEl);
                
                const contentEl = document.createElement('div');
                renderMarkdown(sectionData.content, contentEl); // Use marked to render
                sectionEl.appendChild(contentEl);
                
                reportContentDiv.appendChild(sectionEl);
            }
        });
        
        // Render charts
        if (data.charts && data.charts.length > 0) {
            data.charts.forEach((chartData, index) => {
                if (chartData.labels && chartData.datasets) {
                    const canvas = document.createElement('canvas');
                    canvas.id = `chart-${index}`;
                    chartsContainerDiv.appendChild(canvas);
                    
                    const ctx = canvas.getContext('2d');
                    const newChart = new Chart(ctx, {
                        type: chartData.type || 'bar', // 'bar', 'line', 'pie', etc.
                        data: {
                            labels: chartData.labels,
                            datasets: chartData.datasets.map(ds => ({
                                label: ds.label,
                                data: ds.data,
                                // You can add more styling options here
                                backgroundColor: ds.backgroundColor || getRandomColor(), 
                                borderColor: ds.borderColor || getRandomColor(true),
                                borderWidth: 1
                            }))
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true, // Adjust as needed
                            plugins: {
                                title: {
                                    display: !!chartData.title,
                                    text: chartData.title
                                },
                                legend: {
                                    display: chartData.datasets.length > 1 || (chartData.type === 'pie' || chartData.type === 'doughnut')
                                }
                            },
                            scales: (chartData.type === 'bar' || chartData.type === 'line') ? {
                                y: { beginAtZero: true }
                            } : {}
                        }
                    });
                    chartInstances.push(newChart);
                }
            });
        }


        reportSectionDiv.style.display = 'block';
    }
    
    // Helper function for random chart colors (basic)
    function getRandomColor(isBorder = false) {
        const r = Math.floor(Math.random() * 200);
        const g = Math.floor(Math.random() * 200);
        const b = Math.floor(Math.random() * 200);
        return isBorder ? `rgb(${r},${g},${b})` : `rgba(${r},${g},${b},0.5)`;
    }


    askFollowUpBtn.addEventListener('click', async () => {
        const question = followUpQuestionInput.value.trim();
        if (!question) {
            displayError('Please enter a follow-up question.', followUpErrorMessageDiv);
            return;
        }
        if (!currentReportData || !currentReportData.report_id || !currentReportData.full_text_for_follow_up) {
            displayError('No report context available for follow-up. Please generate a report first.', followUpErrorMessageDiv);
            return;
        }

        clearError(followUpErrorMessageDiv);
        followUpAnswerDiv.innerHTML = '';
        followUpLoadingIndicator.style.display = 'block';
        askFollowUpBtn.disabled = true;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_id: currentReportData.report_id,
                    question: question,
                    report_context: currentReportData.full_text_for_follow_up
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
            }

            const answerData = await response.json();
            renderMarkdown(answerData.answer, followUpAnswerDiv); // Use marked

        } catch (error) {
            console.error('Follow-up error:', error);
            displayError(`Failed to get answer: ${error.message}`, followUpErrorMessageDiv);
        } finally {
            followUpLoadingIndicator.style.display = 'none';
            askFollowUpBtn.disabled = false;
        }
    });

});