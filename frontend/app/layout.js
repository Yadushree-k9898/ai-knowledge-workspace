import './globals.css'

export const metadata = {
  title: 'AI Knowledge & Research Workspace',
  description: 'A production-style modular SaaS application',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
