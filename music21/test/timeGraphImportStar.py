import cProfile
import pstats

def main():
    with cProfile.Profile() as pr:
        import music21

    print(f'Profile of {music21.__version__}')
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats('music21', 0.01)

if __name__ == '__main__':
    main()
