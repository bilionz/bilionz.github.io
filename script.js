// Function to parse URL parameters
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

document.addEventListener('DOMContentLoaded', (event) => {
    // Pre-fill encoded text from URL parameter
    const encodedTextParam = getUrlParameter('encodedText');
    if (encodedTextParam) {
        document.getElementById('encodedText').value = decodeURIComponent(encodedTextParam);
    }
});

async function decodeText() {
    const encodedText = document.getElementById('encodedText').value;
    const publicKeyArmored = document.getElementById('publicKey').value;
    const decodedTextElement = document.getElementById('decodedText');

    try {
        const publicKey = await openpgp.readKey({ armoredKey: publicKeyArmored });
        const message = await openpgp.readMessage({ armoredMessage: encodedText });

        const { data: decrypted } = await openpgp.decrypt({
            message,
            decryptionKeys: publicKey,
        });

        decodedTextElement.textContent = decrypted;
    } catch (error) {
        console.error('Error decoding text:', error);
        decodedTextElement.textContent = 'Failed to decode message.';
    }
}
