from test_fixtures import TestDataFixtures

f = TestDataFixtures()
print('First edge:', f.test_edges[0])
print('Edge type:', type(f.test_edges[0]))
if hasattr(f.test_edges[0], '__len__'):
    print('Edge length:', len(f.test_edges[0]))
print('\nAll edges:')
for i, edge in enumerate(f.test_edges[:3]):  # Just first 3
    print(f'  {i}: {edge}')