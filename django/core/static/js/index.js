
// <!-- Dynamic Checklist Script -->
const checklists = {
		'28': [
				{ text: '補充葉酸', done: true, icon: 'schedule' },
				{ text: '散步 15 分鐘', done: true, icon: 'self_care' },
				{ text: '記錄胎動', done: true, icon: 'event' },
				{ text: '喝水 2000cc', done: true, icon: 'water_drop' },
				{ text: '吃鈣片', done: true, icon: 'medication' },
				{ text: '閱讀孕期知識', done: false, icon: 'menu_book' }
		],
		'29': [
				{ text: '補充葉酸', done: true, icon: 'schedule' },
				{ text: '孕婦瑜伽', done: true, icon: 'self_care' },
				{ text: '測量體重', done: false, icon: 'monitor_weight' },
				{ text: '記錄胎動', done: false, icon: 'event' },
				{ text: '喝水 2000cc', done: false, icon: 'water_drop' },
				{ text: '吃鈣片', done: false, icon: 'medication' }
		],
		'30': [
				{ text: '補充葉酸', done: true, icon: 'schedule' },
				{ text: '定期產檢', done: true, icon: 'event' },
				{ text: '測量血壓', done: true, icon: 'monitor_heart' },
				{ text: '喝水 2000cc', done: false, icon: 'water_drop' },
				{ text: '散步 15 分鐘', done: false, icon: 'self_care' },
				{ text: '吃鈣片', done: false, icon: 'medication' }
		],
		'31': [
				{ text: '補充葉酸', done: true, icon: 'schedule' },
				{ text: '產前運動 20m', done: true, icon: 'self_care' },
				{ text: '產檢提醒', done: false, icon: 'event' },
				{ text: '記錄胎動', done: false, icon: 'monitor_heart' },
				{ text: '喝水 2000cc', done: false, icon: 'water_drop' },
				{ text: '吃鈣片', done: false, icon: 'medication' }
		],
		'1': [
				{ text: '補充葉酸', done: false, icon: 'schedule' },
				{ text: '準備待產包', done: false, icon: 'shopping_bag' },
				{ text: '準備寶寶衣服', done: false, icon: 'checkroom' },
				{ text: '記錄胎動', done: false, icon: 'event' },
				{ text: '喝水 2000cc', done: false, icon: 'water_drop' },
				{ text: '吃鈣片', done: false, icon: 'medication' }
		],
		'2': [
				{ text: '補充葉酸', done: false, icon: 'schedule' },
				{ text: '和寶寶說話', done: false, icon: 'record_voice_over' },
				{ text: '散步 15 分鐘', done: false, icon: 'self_care' },
				{ text: '記錄胎動', done: false, icon: 'event' },
				{ text: '喝水 2000cc', done: false, icon: 'water_drop' },
				{ text: '吃鈣片', done: false, icon: 'medication' }
		],
		'3': [
				{ text: '補充葉酸', done: false, icon: 'schedule' },
				{ text: '參加衛教課程', done: false, icon: 'menu_book' },
				{ text: '孕婦瑜伽', done: false, icon: 'self_care' },
				{ text: '記錄胎動', done: false, icon: 'event' },
				{ text: '喝水 2000cc', done: false, icon: 'water_drop' },
				{ text: '吃鈣片', done: false, icon: 'medication' }
		]
};

const dateBtns = document.querySelectorAll('.date-btn');
const checklistContainer = document.getElementById('checklist-container');
const checklistProgress = document.getElementById('checklist-progress');
const checklistProgressBar = document.getElementById('checklist-progress-bar');


const clToggleBtn = document.getElementById('checklist-toggle-btn');
if (clToggleBtn) {
		clToggleBtn.addEventListener('click', () => {
				const extraItems = document.getElementById('extra-checklist-items');
				if (extraItems) {
						if (extraItems.classList.contains('hidden')) {
								extraItems.classList.remove('hidden');
								extraItems.classList.add('flex');
								clToggleBtn.querySelector('span:first-child').innerText = '收起';
								clToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_up';
						} else {
								extraItems.classList.add('hidden');
								extraItems.classList.remove('flex');
								clToggleBtn.querySelector('span:first-child').innerText = '查看更多';
								clToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_down';
						}
				}
		});
}

window.toggleChecklistItem = function(date, index) {
		if(checklists[date] && checklists[date][index]) {
				checklists[date][index].done = !checklists[date][index].done;

				const extraItems = document.getElementById('extra-checklist-items');
				const isExpanded = extraItems && !extraItems.classList.contains('hidden');

				const activeBtn = document.querySelector('.date-btn.bg-primary');
				if(activeBtn) activeBtn.click();

				if (isExpanded) {
						const newExtraItems = document.getElementById('extra-checklist-items');
						const clToggleBtn = document.getElementById('checklist-toggle-btn');
						if (newExtraItems && clToggleBtn) {
								newExtraItems.classList.remove('hidden');
								newExtraItems.classList.add('flex');
								clToggleBtn.querySelector('span:first-child').innerText = '收起';
								clToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_up';
						}
				}
		}
};

dateBtns.forEach(btn => {
		btn.addEventListener('click', () => {
				// Determine active/inactive baseline classes
				dateBtns.forEach(b => {
						b.classList.remove('bg-primary', 'text-white', 'shadow-lg', 'shadow-primary/30', 'transform', 'scale-105');
						b.classList.add('bg-surface-container-low', 'text-on-surface-variant');
						const spans = b.querySelectorAll('span');
						spans[0].classList.remove('opacity-90');
						spans[1].classList.remove('text-white');
				});

				// Set clicked button to active
				btn.classList.remove('bg-surface-container-low', 'text-on-surface-variant');
				btn.classList.add('bg-primary', 'text-white', 'shadow-lg', 'shadow-primary/30', 'transform', 'scale-105');
				const activeSpans = btn.querySelectorAll('span');
				activeSpans[0].classList.add('opacity-90');
				activeSpans[1].classList.add('text-white');

				// Generate html
				const date = btn.getAttribute('data-date');
				const items = checklists[date] || [];

				let completed = 0;
				let htmlFirst5 = '';
				let htmlRest = '';
				items.forEach((item, index) => {
						if (item.done) completed++;
						const checkIconHtml = item.done ?
								`<div class="w-6 h-6 rounded-md bg-[#d6beff] flex items-center justify-center shrink-0 cursor-pointer" onclick="toggleChecklistItem('${date}', ${index})">
										<span class="material-symbols-outlined text-primary text-sm font-bold">check</span>
								</div>` :
								`<div class="w-6 h-6 rounded-md border-2 border-[#d6beff] shrink-0 cursor-pointer" onclick="toggleChecklistItem('${date}', ${index})"></div>`;
						const textHtml = item.done ?
								`<p class="text-xs font-semibold text-on-surface/50 line-through cursor-pointer" onclick="toggleChecklistItem('${date}', ${index})">${item.text}</p>` :
								`<p class="text-xs font-semibold text-on-surface cursor-pointer" onclick="toggleChecklistItem('${date}', ${index})">${item.text}</p>`;

						const itemHtml = `
								<div class="flex items-center gap-4">
										${checkIconHtml}
										<div class="flex-1 flex items-center gap-2">
												${textHtml}
										</div>
																								<div class="flex gap-1">
												<button onclick="window.location.href='edit_checklist_item.html'" class="text-on-surface-variant/50 hover:bg-primary/10 hover:text-primary p-1 rounded-full transition-colors cursor-pointer">
														<span class="material-symbols-outlined text-[18px]">edit</span>
												</button>
										</div>
								</div>
						`;
						if (index < 5) {
								htmlFirst5 += itemHtml;
						} else {
								htmlRest += itemHtml;
						}
				});

				let finalHtml = htmlFirst5;
				if (items.length > 5) {
						finalHtml += `<div id="extra-checklist-items" class="hidden flex-col gap-4 mt-4">${htmlRest}</div>`;
				}

				const checkToggleBtn = document.getElementById('checklist-toggle-btn');
				if (checkToggleBtn) {
						checkToggleBtn.classList.remove('hidden');
						checkToggleBtn.classList.add('flex');
						if (items.length <= 5) {
								checkToggleBtn.classList.add('hidden');
								checkToggleBtn.classList.remove('flex');
						} else {
								// Reset to default collapsed state when switching date
								checkToggleBtn.querySelector('span:first-child').innerText = '查看更多';
								checkToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_down';
						}
				}

				if (checklistContainer) {
						checklistContainer.innerHTML = finalHtml;
				}
				if (checklistProgress) {
						checklistProgress.innerText = `${completed}/${items.length}`;
				}
				if (checklistProgressBar) {
						const percentage = items.length ? (completed / items.length) * 100 : 0;
						checklistProgressBar.style.width = `${percentage}%`;
				}
		});
});

// <!-- Scroll Restoration Script -->
window.addEventListener('load', () => {
		const savedScrollPos = sessionStorage.getItem('scrollPos');
		if (savedScrollPos !== null) {
				window.scrollTo({
						top: parseInt(savedScrollPos, 10),
						behavior: 'instant'
				});
				sessionStorage.removeItem('scrollPos');
		}

		// Initialize the checklist with the active date
		const activeDateBtn = document.querySelector('.date-btn.bg-primary');
		if(activeDateBtn) {
				activeDateBtn.click();
		}
});


