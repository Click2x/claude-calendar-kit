import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

// The pet's current line, exactly as `cal.py pet say` prints it ("" when the pet is off or the calendar is not installed).
const line = atom({ plugin: 'calendar-pet', key: 'line' } as const, '')

async function refresh($: any) {
  const home = (await $.env.get('HOME')) || (await $.env.get('USERPROFILE'))
  if (!home) return
  const cal = String(home).split(String.fromCharCode(92)).join('/') + '/.claude/calendar/cal.py'
  for (const py of ['python', 'py', 'python3']) {
    try {
      const out = await $.process.run([py, cal, 'pet', 'say'], { timeoutMs: 10000 })
      if (out.exitCode === 0) {
        await update($, line, () => out.stdout.trim())
        return
      }
    } catch {
      // try the next interpreter name
    }
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await refresh($)
    return next(e)
  })
  on('prompt.submit', async ($, e, next) => {
    await refresh($)
    return next(e)
  })
  on('turn.complete', async ($, e, next) => {
    await refresh($)
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const text = await read($, line)
    if (e.props.hasSurvey || !text) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box>
        <Text color="magenta">{text}</Text>
      </Box>
    )
  })
}
