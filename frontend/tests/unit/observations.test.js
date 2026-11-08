import { describe, expect, it } from 'vitest'

import { groupObservations } from '../../src/utils/observations'

const marker = (id, time, text = id) => ({
  id,
  time,
  text,
  segmentId: `segment-${id}`,
  type: 'observacion',
})

describe('groupObservations', () => {
  it('agrupa observaciones visualmente próximas', () => {
    const groups = groupObservations(
      [marker('a', 0), marker('b', 0.5), marker('c', 1)],
      100,
      100,
    )

    expect(groups).toHaveLength(1)
    expect(groups[0].count).toBe(3)
    expect(groups[0].observations.map((item) => item.id)).toEqual(['a', 'b', 'c'])
    expect(groups[0].position_ratio).toBe(0)
  })

  it('separa observaciones cuando superan el umbral de 14 px', () => {
    const groups = groupObservations(
      [marker('a', 0), marker('b', 50), marker('c', 100)],
      100,
      100,
    )

    expect(groups).toHaveLength(3)
    expect(groups.map((group) => group.count)).toEqual([1, 1, 1])
  })

  it('mantiene el límite exacto de 14 px dentro del mismo grupo', () => {
    const groups = groupObservations([marker('a', 0), marker('b', 1.3)], 1000, 100)

    expect(groups).toHaveLength(1)
    expect(groups[0].count).toBe(2)
  })

  it('separa un píxel por encima del umbral', () => {
    const groups = groupObservations([marker('a', 0), marker('b', 1.5)], 1000, 100)

    expect(groups).toHaveLength(2)
  })

  it('agrupa observaciones con el mismo timestamp', () => {
    const groups = groupObservations([marker('a', 10), marker('b', 10)], 100, 100)

    expect(groups).toHaveLength(1)
    expect(groups[0].count).toBe(2)
  })

  it('usa el mismo formato para una sola observación', () => {
    const groups = groupObservations([marker('a', 10)], 100, 100)

    expect(groups).toHaveLength(1)
    expect(groups[0].count).toBe(1)
    expect(groups[0].id).toBe('group-a')
  })

  it('devuelve una lista vacía sin marcadores', () => {
    expect(groupObservations([], 100, 100)).toEqual([])
  })
})
