// --- Segmented Control Logic ---
function updateRoleInput() {
		let isCaregiver = false;
		document.querySelectorAll('.perm-group').forEach(group => {
				const activeBtn = group.querySelector('.bg-white');
				if (activeBtn && activeBtn.dataset.val === 'caregiver') {
						isCaregiver = true;
				}
		});
		const roleEl = document.getElementById('form-role');
		if (roleEl) {
				// Keep 'mom' role intact, otherwise toggle caregiver/viewer based on selections
				if (roleEl.value !== 'mom') {
						roleEl.value = isCaregiver ? 'caregiver' : 'viewer';
				}
		}
}

document.querySelectorAll('.perm-group').forEach(group => {
		const btns = group.querySelectorAll('.perm-btn');
		btns.forEach(btn => {
				btn.addEventListener('click', () => {
						// Reset all buttons in group
						btns.forEach(b => {
								b.classList.remove('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
								b.classList.add('text-on-surface-variant', 'hover:bg-surface-container-high/50');
						});
						// Set active state for clicked button
						btn.classList.add('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
						btn.classList.remove('text-on-surface-variant', 'hover:bg-surface-container-high/50');
						updateRoleInput();
				});
		});
});

// Initialize UI based on current role
const formRoleEl = document.getElementById('form-role');
if (formRoleEl) {
		const currentRole = formRoleEl.value;
		document.querySelectorAll('.perm-group').forEach(group => {
				const btns = group.querySelectorAll('.perm-btn');
				btns.forEach(btn => {
						if (btn.dataset.val === currentRole || (currentRole === 'mom' && btn.dataset.val === 'caregiver')) {
								btn.classList.add('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
								btn.classList.remove('text-on-surface-variant', 'hover:bg-surface-container-high/50');
						} else {
								btn.classList.remove('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
								btn.classList.add('text-on-surface-variant', 'hover:bg-surface-container-high/50');
						}
				});
		});
}

// Modal Logic
const helperBtn = document.getElementById('helper-selector-btn');
const helperModal = document.getElementById('helper-modal');
const helperModalBackdrop = document.getElementById('helper-modal-backdrop');
const helperModalContent = document.getElementById('helper-modal-content');
const closeHelperModal = document.getElementById('close-helper-modal');
const helperOptions = document.querySelectorAll('.helper-option');

const currentHelperName = document.getElementById('current-helper-name');
const currentHelperRole = document.getElementById('current-helper-role');
const currentHelperIcon = document.getElementById('current-helper-icon');
const formMemberId = document.getElementById('form-member-id');

if (helperBtn) {
		function openModal() {
				helperModal.classList.remove('opacity-0', 'pointer-events-none');
				helperModal.classList.add('opacity-100', 'pointer-events-auto');

				// Animation for modal content
				setTimeout(() => {
						helperModalContent.classList.remove('translate-y-full', 'sm:translate-y-4', 'sm:scale-95');
						helperModalContent.classList.add('translate-y-0', 'sm:translate-y-0', 'sm:scale-100');
				}, 10);
		}

		function closeModal() {
				helperModalContent.classList.remove('translate-y-0', 'sm:translate-y-0', 'sm:scale-100');
				helperModalContent.classList.add('translate-y-full', 'sm:translate-y-4', 'sm:scale-95');

				setTimeout(() => {
						helperModal.classList.remove('opacity-100', 'pointer-events-auto');
						helperModal.classList.add('opacity-0', 'pointer-events-none');
				}, 300);
		}

		helperBtn.addEventListener('click', openModal);
		closeHelperModal.addEventListener('click', closeModal);
		helperModalBackdrop.addEventListener('click', closeModal);

		helperOptions.forEach(option => {
				option.addEventListener('click', () => {
						// Update styling for all options
						helperOptions.forEach(opt => {
								opt.classList.remove('bg-primary/5', 'border-primary/20', 'border');
								opt.classList.add('bg-surface-container-low/50', 'hover:bg-surface-container-low', 'border-transparent');

								const nameSpan = opt.querySelector('.helper-name-span');
								nameSpan.classList.remove('text-primary');
								nameSpan.classList.add('text-on-surface');

								const roleSpan = opt.querySelector('.helper-role-span');
								roleSpan.classList.remove('text-primary/70');
								roleSpan.classList.add('text-on-surface-variant');

								const checkIcon = opt.querySelector('.check-icon');
								checkIcon.classList.remove('text-primary');
								checkIcon.classList.add('text-transparent');
						});

						// Set styling for selected option
						option.classList.remove('bg-surface-container-low/50', 'hover:bg-surface-container-low', 'border-transparent');
						option.classList.add('bg-primary/5', 'border-primary/20', 'border');

						const nameSpan = option.querySelector('.helper-name-span');
						nameSpan.classList.remove('text-on-surface');
						nameSpan.classList.add('text-primary');

						const roleSpan = option.querySelector('.helper-role-span');
						roleSpan.classList.remove('text-on-surface-variant');
						roleSpan.classList.add('text-primary/70');

						const checkIcon = option.querySelector('.check-icon');
						checkIcon.classList.remove('text-transparent');
						checkIcon.classList.add('text-primary');

						// Update main button display
						currentHelperName.textContent = option.dataset.name;
						currentHelperRole.textContent = '(' + option.dataset.role + ')';
						currentHelperIcon.textContent = option.dataset.icon;
						formMemberId.value = option.dataset.id;

						// Auto update UI role buttons based on selected user's role
						formRoleEl.value = option.dataset.role;
						document.querySelectorAll('.perm-group').forEach(group => {
								const btns = group.querySelectorAll('.perm-btn');
								btns.forEach(btn => {
										if (btn.dataset.val === formRoleEl.value || (formRoleEl.value === 'mom' && btn.dataset.val === 'caregiver')) {
												btn.classList.add('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
												btn.classList.remove('text-on-surface-variant', 'hover:bg-surface-container-high/50');
										} else {
												btn.classList.remove('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
												btn.classList.add('text-on-surface-variant', 'hover:bg-surface-container-high/50');
										}
								});
						});

						// Provide haptic feedback
						if (window.navigator && window.navigator.vibrate) {
								window.navigator.vibrate(50);
						}

						setTimeout(() => {
								closeModal();
						}, 150);
				});
		});
}
