document.addEventListener('DOMContentLoaded', () => {

    async function fetchAPI(url, options = {}) {
        try {
            const response = await fetch(url, options);
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    }

    // --- PAGE: INDEX ---
    const subjectForm = document.getElementById('subjectForm');
    const topicForm = document.getElementById('topicForm');
    const topicSubjectId = document.getElementById('topicSubjectId');
    const generateScheduleBtn = document.getElementById('generateScheduleBtn');

    if (subjectForm) {
        async function loadSubjectsForSelect() {
            const subjects = await fetchAPI('/api/subjects');
            if (subjects && topicSubjectId) {
                topicSubjectId.innerHTML = '<option value="" disabled selected>Select Subject...</option>';
                subjects.forEach(sub => {
                    const opt = document.createElement('option');
                    opt.value = sub.id;
                    opt.textContent = sub.name;
                    topicSubjectId.appendChild(opt);
                });
            }
        }
        loadSubjectsForSelect();

        subjectForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('subjectName').value,
                exam_date: document.getElementById('examDate').value,
                daily_hours_allocated: document.getElementById('dailyHours').value
            };
            const result = await fetchAPI('/api/subjects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            alert(result.message);
            subjectForm.reset();
            loadSubjectsForSelect();
        });

        topicForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                subject_id: topicSubjectId.value,
                name: document.getElementById('topicName').value,
                difficulty: document.getElementById('topicDifficulty').value
            };
            const result = await fetchAPI('/api/topics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            alert(result.message);
            topicForm.reset();
        });

        generateScheduleBtn.addEventListener('click', async () => {
             const msg = document.getElementById('generateMsg');
             msg.textContent = "AI is generating your optimal plan...";
             const result = await fetchAPI('/api/schedule/generate', { method: 'POST' });
             if (result.error) {
                 msg.textContent = result.error;
                 msg.style.color = "#F43F5E"; // Deep Red for fail
             } else {
                 msg.textContent = result.message;
                 msg.style.color = "#10B981"; // Emerald green for success
                 setTimeout(() => {
                     window.location.href = '/schedule_view';
                 }, 1500);
             }
        });
    }

    // --- PAGE: SCHEDULE VIEW ---
    const scheduleContainer = document.getElementById('scheduleContainer');
    if (scheduleContainer) {
        async function loadSchedule() {
            const plan = await fetchAPI('/api/schedule');
            if (!plan || plan.length === 0) {
                scheduleContainer.innerHTML = '<h3 style="text-align:center; color: #94A3B8;">No schedule blocks found. Did you generate your plan?</h3>';
                return;
            }

            const grouped = {};
            plan.forEach(item => {
                if (!grouped[item.date]) grouped[item.date] = [];
                grouped[item.date].push(item);
            });

            scheduleContainer.innerHTML = '';
            
            for (const [date, tasks] of Object.entries(grouped)) {
                
                const dateObj = new Date(date);
                const displayDate = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

                const block = document.createElement('div');
                block.className = 'day-block fade-in';
                block.innerHTML = `<h2 class="day-header">✦ ${displayDate}</h2>`;
                
                tasks.forEach(task => {
                    const tCard = document.createElement('div');
                    tCard.className = `task-card ${task.is_revision ? 'revision' : ''} ${task.is_completed ? 'completed' : ''}`;
                    
                    const badge = task.is_revision ? '<span class="badge-tag">Spaced Revision</span>' : '';
                    let diffStars = '⚡'.repeat(task.difficulty);

                    tCard.innerHTML = `
                        <div>
                            <div style="font-size: 1.4rem; font-weight: 600; color: white; display:flex; align-items:center; gap: 10px;">
                                ${task.topic_name}
                                ${badge}
                            </div>
                            <div style="color:var(--secondary-text); margin-top:8px; font-size: 1.05rem; display:flex; align-items:center; gap: 15px;">
                                <span style="color:#A78BFA">• ${task.subject_name}</span> 
                                <span>Load: ${diffStars}</span>
                            </div>
                        </div>
                        <div>
                            ${task.is_completed 
                                ? '<span style="color:#10B981; font-weight:600; font-size: 1.1rem;">✓ Task Done</span>' 
                                : `<button class="action-btn" onclick="markComplete(${task.id})">Mark Complete</button>`
                            }
                        </div>
                    `;
                    block.appendChild(tCard);
                });
                scheduleContainer.appendChild(block);
            }
        }
        loadSchedule();

        window.markComplete = async function(id) {
            const result = await fetchAPI(`/api/schedule/${id}/complete`, { method: 'PUT' });
            if(result) {
                loadSchedule();
            }
        };
    }

    // --- PAGE: PROGRESS VIEW ---
    const topicsContainer = document.getElementById('topicsContainer');
    if (topicsContainer) {
        async function loadProgress() {
            const topics = await fetchAPI('/api/topics');
            if (!topics || topics.length === 0) {
                topicsContainer.innerHTML = '<div style="text-align:center; padding: 20px; color: #94A3B8;">No trajectory data found.</div>';
                return;
            }
            topicsContainer.innerHTML = '';
            topics.forEach(t => {
                const diffLabels = {1: 'Level 1', 2: 'Level 2', 3: 'Level 3'};
                const isPending = t.status === 'Pending';
                
                topicsContainer.innerHTML += `
                    <div class="status-row fade-in">
                        <div style="flex:1.5; font-size: 1.1rem; color: white; font-weight:500;">${t.name}</div>
                        <div style="flex:1; color: #A78BFA; font-weight: 500;">${t.subject_name}</div>
                        <div style="flex:1; color: var(--secondary-text);">${diffLabels[t.difficulty]}</div>
                        <div style="flex:0.5; text-align:right;">
                            <span class="badge ${isPending ? 'pending' : 'done'}">
                                ${isPending ? 'In Progress' : 'Mastered'}
                            </span>
                        </div>
                    </div>
                `;
            });
        }
        loadProgress();
    }
});
