/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: process.env.API_GATEWAY_URL || 'http://api-gateway:8000/:path*',
            },
        ]
    },
}

module.exports = nextConfig
