import SyntheticBanner from './SyntheticBanner'
import WorkspaceHeader from './WorkspaceHeader'

export default function WorkspaceLayout({
  session,
  onNewInterview,
  onExport,
  exporting = false,
  children,
}) {
  return (
    <div className="workspace">
      <WorkspaceHeader
        session={session}
        onNewInterview={onNewInterview}
        onExport={onExport}
        exporting={exporting}
      />
      <main className="workspace__main">
        <SyntheticBanner />
        {children}
      </main>
    </div>
  )
}
