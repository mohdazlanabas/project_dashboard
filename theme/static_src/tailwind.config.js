/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        '../../../**/templates/**/*.html', // Scans templates in any app
        '../../../../templates/**/*.html', // Scans templates in the root templates folder
    ],
    theme: {
        extend: {},
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a basic reset for
         * form styles that makes form elements easy to override with utilities.
         *
         * https://github.com/tailwindlabs/tailwindcss-forms
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}