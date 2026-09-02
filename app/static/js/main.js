let currentSnapshots = [];
let currentIndex = 0;

async function openSnapshotModal(pageId, url) {
    const modal = document.getElementById('snapshot_modal');
    const urlEl = document.getElementById('modal-url');
    const textEl = document.getElementById('snapshot-text');
    const dateEl = document.getElementById('snapshot-date');
    const currentNumEl = document.getElementById('current-snapshot-num');
    const totalNumEl = document.getElementById('total-snapshots');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');


    urlEl.textContent = url;
    textEl.textContent = 'Loading snapshots...';
    dateEl.textContent = '...';
    currentNumEl.textContent = '0';
    totalNumEl.textContent = '0';
    btnPrev.disabled = true;
    btnNext.disabled = true;


    modal.showModal();

    try {

        const response = await fetch(`/api/v1/tracked-pages/${pageId}/snapshots`);
        if (!response.ok) throw new Error('Failed to fetch data');

        currentSnapshots = await response.json();

        if (currentSnapshots.length === 0) {
            textEl.textContent = 'No snapshots found for this page yet.';
            return;
        }


        currentIndex = 0;
        renderSnapshot();

    } catch (error) {
        textEl.textContent = 'Error loading snapshots. Please try again later.';
        console.error(error);
    }
}

function renderSnapshot() {
    if (currentSnapshots.length === 0) return;

    const snap = currentSnapshots[currentIndex];
    const textEl = document.getElementById('snapshot-text');
    textEl.innerHTML = '';

    // If there is an older snapshot and Diff library is loaded
    if (currentIndex < currentSnapshots.length - 1 && typeof Diff !== 'undefined') {
        const olderSnap = currentSnapshots[currentIndex + 1];
        const diff = Diff.diffWords(olderSnap.content_text || '', snap.content_text || '');
        
        let fragment = document.createDocumentFragment();
        diff.forEach((part) => {
            const span = document.createElement('span');
            if (part.added) {
                span.classList.add('bg-success/20', 'text-success', 'font-semibold', 'px-1', 'rounded', 'mx-px');
            } else if (part.removed) {
                span.classList.add('bg-error/20', 'text-error', 'line-through', 'opacity-75', 'px-1', 'rounded', 'mx-px');
            }
            span.appendChild(document.createTextNode(part.value));
            fragment.appendChild(span);
        });
        textEl.appendChild(fragment);
    } else {
        // Oldest snapshot or only one snapshot
        textEl.textContent = snap.content_text || 'No content available';
    }


    const dateObj = new Date(snap.created_at);
    document.getElementById('snapshot-date').textContent = dateObj.toLocaleString();


    document.getElementById('current-snapshot-num').textContent = currentSnapshots.length - currentIndex;
    document.getElementById('total-snapshots').textContent = currentSnapshots.length;


    // currentIndex 0 is the NEWEST
    document.getElementById('btn-prev').disabled = currentIndex >= currentSnapshots.length - 1;
    document.getElementById('btn-next').disabled = currentIndex <= 0;
}


document.addEventListener('DOMContentLoaded', () => {

    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');


    if (btnPrev) {
        btnPrev.addEventListener('click', () => {
            if (currentIndex < currentSnapshots.length - 1) {
                currentIndex++;
                renderSnapshot();
            }
        });
    }


    if (btnNext) {
        btnNext.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                renderSnapshot();
            }
        });
    }
});


document.addEventListener('htmx:afterRequest', (event) => {

    const elt = event.target;



    if (!elt.matches('button[data-archive-action]')) return;


    if (!event.detail.successful) return;

    const action = elt.dataset.archiveAction;
    const card = elt.closest('.card');
    if (!card) return;

    if (action === 'archive') {

        card.classList.remove('bg-base-100');
        card.classList.add('opacity-60', 'bg-base-200', 'order-last');
    } else if (action === 'activate') {

        card.classList.remove('opacity-60', 'bg-base-200', 'order-last');
        card.classList.add('bg-base-100');
    }
});
