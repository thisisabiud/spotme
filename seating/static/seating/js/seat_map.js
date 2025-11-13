function highlightSeatById(seatId) {
    const marker = document.querySelector(`[data-seat-id="${seatId}"]`);
    if (marker) {
        // Add highlight animation
        marker.style.animation = 'pulse 2s infinite';
        marker.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Remove animation after 6 seconds
        setTimeout(() => {
            marker.style.animation = '';
        }, 6000);
    }
}

function searchAndHighlight(attendeeName) {
    const markers = document.querySelectorAll('.seat-marker');
    markers.forEach(marker => {
        if (marker.dataset.attendee.toLowerCase().includes(attendeeName.toLowerCase())) {
            highlightSeatById(marker.dataset.seatId);
        }
    });
}

// Add CSS animation for pulsing effect
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { 
            transform: translate(-50%, -50%) scale(1);
            box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);
        }
        70% { 
            transform: translate(-50%, -50%) scale(1.1);
            box-shadow: 0 0 0 10px rgba(255, 0, 0, 0);
        }
        100% { 
            transform: translate(-50%, -50%) scale(1);
            box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);
        }
    }
`;
document.head.appendChild(style);